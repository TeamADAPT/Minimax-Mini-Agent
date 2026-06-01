use async_nats::Client;
use futures_util::StreamExt;
use nova_crew_consensus::{
    run_consensus_service_with_ready, ConsensusConfig, ProposalPayload, VoteDecision, VotePayload,
};
use serde_json::Value;
use std::net::{SocketAddr, TcpListener};
use std::process::{Child, Command, Stdio};
use std::time::Duration;
use tokio::net::TcpStream;
use tokio::sync::oneshot;
use tokio::time::{sleep, timeout};

#[tokio::test]
async fn real_nats_bind_and_timeout_flows() -> anyhow::Result<()> {
    let Some(mut server) = NatsServer::start().await? else {
        return Ok(());
    };
    let client = async_nats::connect(server.url()).await?;
    let config = ConsensusConfig::new(
        "testnova",
        ["skipper", "echo", "synergy"]
            .into_iter()
            .map(ToOwned::to_owned),
    )?
    .with_poll_interval(Duration::from_millis(10));

    let (shutdown_tx, shutdown_rx) = oneshot::channel::<()>();
    let (ready_tx, ready_rx) = oneshot::channel::<()>();
    let service_task = tokio::spawn(run_consensus_service_with_ready(
        client.clone(),
        config.clone(),
        ready_tx,
        async {
            let _ = shutdown_rx.await;
        },
    ));
    timeout(Duration::from_secs(3), ready_rx).await??;

    let bind = run_bind_proof(&client, &config).await?;
    assert_eq!(bind["decision"], "BIND");
    assert_eq!(bind["yes_votes"], 2);

    let timeout_result = run_timeout_proof(&client, &config).await?;
    assert_eq!(timeout_result["decision"], "NO_QUORUM");
    assert_eq!(timeout_result["yes_votes"], 2);

    let _ = shutdown_tx.send(());
    timeout(Duration::from_secs(2), service_task).await???;
    server.stop()?;
    Ok(())
}

async fn run_bind_proof(client: &Client, config: &ConsensusConfig) -> anyhow::Result<Value> {
    let mut sub = client
        .subscribe(config.bind_subject("deploy-rust-bridge-v1"))
        .await?;
    client.flush().await?;
    let proposal_id = "rust-bind-proof-001";
    publish_proposal(client, config, "deploy-rust-bridge-v1", proposal_id, 2, 3).await?;
    publish_vote(client, config, proposal_id, "skipper").await?;
    publish_vote(client, config, proposal_id, "echo").await?;
    let msg = timeout(Duration::from_secs(3), sub.next()).await?;
    Ok(serde_json::from_slice(
        &msg.ok_or_else(|| anyhow::anyhow!("bind subscription closed"))?
            .payload,
    )?)
}

async fn run_timeout_proof(client: &Client, config: &ConsensusConfig) -> anyhow::Result<Value> {
    let mut sub = client
        .subscribe(config.bind_subject("timeout-case"))
        .await?;
    client.flush().await?;
    let proposal_id = "rust-timeout-proof-001";
    publish_proposal(client, config, "timeout-case", proposal_id, 3, 1).await?;
    publish_vote(client, config, proposal_id, "skipper").await?;
    publish_vote(client, config, proposal_id, "echo").await?;
    let msg = timeout(Duration::from_secs(4), sub.next()).await?;
    Ok(serde_json::from_slice(
        &msg.ok_or_else(|| anyhow::anyhow!("timeout subscription closed"))?
            .payload,
    )?)
}

async fn publish_proposal(
    client: &Client,
    config: &ConsensusConfig,
    topic: &str,
    proposal_id: &str,
    quorum: usize,
    timeout_seconds: u64,
) -> anyhow::Result<()> {
    let proposal = ProposalPayload {
        topic: topic.to_string(),
        proposer: "synergy".to_string(),
        proposal_id: Some(proposal_id.to_string()),
        evidence: "integration proof".to_string(),
        quorum,
        timeout_seconds,
    };
    client
        .publish(
            config.propose_subject(),
            serde_json::to_vec(&proposal)?.into(),
        )
        .await?;
    Ok(())
}

async fn publish_vote(
    client: &Client,
    config: &ConsensusConfig,
    proposal_id: &str,
    voter: &str,
) -> anyhow::Result<()> {
    let vote = VotePayload {
        proposal_id: Some(proposal_id.to_string()),
        topic: None,
        voter: Some(voter.to_string()),
        decision: VoteDecision::Yes,
        reasoning: "integration proof".to_string(),
    };
    client
        .publish(
            format!("{}.crew.consensus.vote.{voter}", config.namespace()),
            serde_json::to_vec(&vote)?.into(),
        )
        .await?;
    Ok(())
}

struct NatsServer {
    child: Child,
    addr: SocketAddr,
}

impl NatsServer {
    async fn start() -> anyhow::Result<Option<Self>> {
        let binary = Command::new("bash")
            .arg("-lc")
            .arg("command -v nats-server")
            .stdout(Stdio::piped())
            .output()?;
        let path = String::from_utf8(binary.stdout)?.trim().to_string();
        if path.is_empty() {
            eprintln!("nats-server not available; skipping real NATS consensus proof");
            return Ok(None);
        }

        let addr = free_addr()?;
        let child = Command::new(path)
            .arg("-a")
            .arg(addr.ip().to_string())
            .arg("-p")
            .arg(addr.port().to_string())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()?;
        wait_for_port(addr).await?;
        Ok(Some(Self { child, addr }))
    }

    fn url(&self) -> String {
        format!("nats://{}", self.addr)
    }

    fn stop(&mut self) -> anyhow::Result<()> {
        self.child.kill()?;
        let _ = self.child.wait()?;
        Ok(())
    }
}

impl Drop for NatsServer {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

fn free_addr() -> anyhow::Result<SocketAddr> {
    let listener = TcpListener::bind("127.0.0.1:0")?;
    let addr = listener.local_addr()?;
    drop(listener);
    Ok(addr)
}

async fn wait_for_port(addr: SocketAddr) -> anyhow::Result<()> {
    let deadline = tokio::time::Instant::now() + Duration::from_secs(5);
    while tokio::time::Instant::now() < deadline {
        if TcpStream::connect(addr).await.is_ok() {
            return Ok(());
        }
        sleep(Duration::from_millis(25)).await;
    }
    anyhow::bail!("nats-server did not open {addr}")
}
