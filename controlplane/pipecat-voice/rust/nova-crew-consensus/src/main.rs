//! Command-line entrypoint for the Nova crew consensus service.

use anyhow::{Context, Result};
use async_nats::ConnectOptions;
use clap::{Parser, Subcommand};
use futures_util::StreamExt;
use nova_crew_consensus::{
    run_consensus_service, run_consensus_service_with_ready, ConsensusConfig, ProposalPayload,
    VoteDecision, VotePayload,
};
use std::path::Path;
use std::time::Duration;
use tokio::sync::oneshot;
use tokio::time::timeout;
use tracing::{info, warn};
use tracing_subscriber::EnvFilter;

#[derive(Debug, Parser)]
#[command(name = "nova-crew-consensus")]
#[command(about = "Rust NATS consensus service for Nova crew propose/vote/bind decisions")]
struct Args {
    #[arg(long, env = "NATS_URL")]
    nats_url: Option<String>,

    #[arg(long, env = "NATS_USER")]
    nats_user: Option<String>,

    #[arg(long, env = "NATS_PASSWORD")]
    nats_password: Option<String>,

    #[arg(long, env = "SUBJECT_NS", default_value = "nova")]
    namespace: String,

    #[arg(long, env = "CONSENSUS_VOTERS", value_delimiter = ',')]
    voters: Vec<String>,

    #[arg(long, env = "CONSENSUS_POLL_MS", default_value_t = 250)]
    poll_ms: u64,

    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Run the long-lived subscriber service.
    Serve,
    /// Run a bounded real-NATS proof and print the resolution JSON.
    Prove {
        #[arg(long, default_value = "deploy-rust-bridge-v1")]
        topic: String,
        #[arg(long, default_value = "rust-proof-001")]
        proposal_id: String,
        #[arg(long, default_value_t = 2)]
        quorum: usize,
        #[arg(long, default_value_t = 2)]
        timeout_seconds: u64,
        #[arg(long, value_delimiter = ',', default_value = "skipper,echo,synergy")]
        yes_voters: Vec<String>,
        #[arg(long, default_value_t = false)]
        expect_timeout: bool,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    init_tracing();
    let args = Args::parse();
    let config = build_config(&args)?;
    match &args.command {
        Command::Serve => serve(&args, config).await,
        Command::Prove {
            topic,
            proposal_id,
            quorum,
            timeout_seconds,
            yes_voters,
            expect_timeout,
        } => {
            let proof = ProofConfig {
                topic,
                proposal_id,
                quorum: *quorum,
                timeout_seconds: *timeout_seconds,
                yes_voters,
                expect_timeout: *expect_timeout,
            };
            prove(&args, config, proof).await
        }
    }
}

async fn serve(args: &Args, config: ConsensusConfig) -> Result<()> {
    let client = connect(args, "nova-crew-consensus")
        .await
        .context("connect to NATS for consensus service")?;
    info!(
        namespace = config.namespace(),
        voters = ?config.voters(),
        "crew consensus service starting"
    );
    run_consensus_service(client, config, async {
        if let Err(err) = tokio::signal::ctrl_c().await {
            warn!(error = %err, "ctrl-c listener failed; shutting down");
        }
    })
    .await
    .context("run consensus service")
}

struct ProofConfig<'a> {
    topic: &'a str,
    proposal_id: &'a str,
    quorum: usize,
    timeout_seconds: u64,
    yes_voters: &'a [String],
    expect_timeout: bool,
}

async fn prove(args: &Args, config: ConsensusConfig, proof: ProofConfig<'_>) -> Result<()> {
    let client = connect(args, "nova-crew-consensus-proof")
        .await
        .context("connect to NATS for consensus proof")?;
    let service_client = client.clone();
    let (shutdown_tx, shutdown_rx) = oneshot::channel::<()>();
    let (ready_tx, ready_rx) = oneshot::channel::<()>();
    let service_config = config.clone();
    let service_task = tokio::spawn(async move {
        let _ = run_consensus_service_with_ready(service_client, service_config, ready_tx, async {
            let _ = shutdown_rx.await;
        })
        .await;
    });

    timeout(Duration::from_secs(3), ready_rx)
        .await
        .context("timed out waiting for proof service subscriptions")?
        .context("proof service stopped before subscriptions were ready")?;
    let bind_subject = config.bind_subject(proof.topic);
    let mut bind_sub = client
        .subscribe(bind_subject)
        .await
        .context("subscribe to proof bind subject")?;
    client
        .flush()
        .await
        .context("flush proof bind subscription")?;

    let proposal = ProposalPayload {
        topic: proof.topic.to_string(),
        proposer: "synergy".to_string(),
        proposal_id: Some(proof.proposal_id.to_string()),
        evidence: "nova-crew-consensus bounded proof".to_string(),
        quorum: proof.quorum,
        timeout_seconds: proof.timeout_seconds,
    };
    client
        .publish(
            config.propose_subject(),
            serde_json::to_vec(&proposal)
                .context("encode proof proposal")?
                .into(),
        )
        .await
        .context("publish proof proposal")?;

    let votes_to_publish = if proof.expect_timeout {
        proof.yes_voters.iter().take(proof.quorum.saturating_sub(1))
    } else {
        proof.yes_voters.iter().take(proof.quorum)
    };
    for voter in votes_to_publish {
        let vote = VotePayload {
            proposal_id: Some(proof.proposal_id.to_string()),
            topic: None,
            voter: Some(voter.to_string()),
            decision: VoteDecision::Yes,
            reasoning: "bounded proof vote".to_string(),
        };
        client
            .publish(
                format!("{}.crew.consensus.vote.{voter}", config.namespace()),
                serde_json::to_vec(&vote)
                    .context("encode proof vote")?
                    .into(),
            )
            .await
            .context("publish proof vote")?;
    }

    let wait = Duration::from_secs(proof.timeout_seconds.saturating_add(3).max(3));
    let msg = timeout(wait, bind_sub.next())
        .await
        .context("timed out waiting for consensus proof result")?
        .context("proof bind subscription closed")?;
    let value: serde_json::Value =
        serde_json::from_slice(&msg.payload).context("decode proof resolution")?;
    println!("{}", serde_json::to_string_pretty(&value)?);
    let _ = shutdown_tx.send(());
    let _ = timeout(Duration::from_secs(2), service_task).await;
    Ok(())
}

async fn connect(args: &Args, name: &str) -> Result<async_nats::Client> {
    let url = args
        .nats_url
        .clone()
        .or_else(|| std::env::var("NATS_URL").ok())
        .or_else(|| read_env_value(Path::new("/adapt/secrets/db.env"), "NATS_URL"))
        .unwrap_or_else(|| "nats://127.0.0.1:18020".to_string());
    let mut options = ConnectOptions::new().name(name.to_string());
    if let (Some(user), Some(password)) = (
        args.nats_user
            .clone()
            .or_else(|| std::env::var("NATS_USER").ok()),
        args.nats_password
            .clone()
            .or_else(|| std::env::var("NATS_PASSWORD").ok()),
    ) {
        options = options.user_and_password(user, password);
    }
    options.connect(url).await.context("open NATS connection")
}

fn build_config(args: &Args) -> Result<ConsensusConfig> {
    let voters = if args.voters.is_empty() {
        nova_crew_consensus::DEFAULT_VOTERS
            .iter()
            .map(|voter| (*voter).to_string())
            .collect()
    } else {
        args.voters.clone()
    };
    ConsensusConfig::new(args.namespace.clone(), voters)
        .map(|config| config.with_poll_interval(Duration::from_millis(args.poll_ms)))
        .context("build consensus config")
}

fn read_env_value(path: &Path, key: &str) -> Option<String> {
    let text = std::fs::read_to_string(path).ok()?;
    text.lines().find_map(|line| {
        let line = line.trim();
        if line.starts_with('#') || !line.starts_with(key) {
            return None;
        }
        let (_, value) = line.split_once('=')?;
        Some(
            value
                .trim()
                .trim_matches('"')
                .trim_matches('\'')
                .to_string(),
        )
    })
}

fn init_tracing() {
    let filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));
    tracing_subscriber::fmt()
        .with_env_filter(filter)
        .with_writer(std::io::stderr)
        .json()
        .init();
}
