use anyhow::{Context, Result};
use async_nats::{Client, ConnectOptions, Subscriber};
use clap::Parser;
use futures_util::StreamExt;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Stdio;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use thiserror::Error;
use tokio::process::Command;
use tokio::sync::mpsc;
use tokio::time::timeout;
use tracing::{error, info, warn};

#[derive(Parser, Debug, Clone)]
#[command(name = "nova-hermes-nats-bridge")]
#[command(about = "Rust NATS subject owner for Nova Hermes profiles")]
struct Args {
    #[arg(long, env = "NATS_URL", default_value = "127.0.0.1:18020")]
    nats_url: String,

    #[arg(long, env = "NATS_USER")]
    nats_user: Option<String>,

    #[arg(long, env = "NATS_PASSWORD")]
    nats_password: Option<String>,

    #[arg(long, env = "NATS_AGENT_NAME", default_value = "echo")]
    agent: String,

    #[arg(long, env = "NOVA_DIRECT_SUBJECT")]
    direct_subject: Option<String>,

    #[arg(long, env = "NOVA_MEET_SUBJECT")]
    meet_subject: Option<String>,

    #[arg(long, env = "NOVA_PING_SUBJECT")]
    ping_subject: Option<String>,

    #[arg(long, env = "SUBJECT_NS", default_value = "nova")]
    subject_prefix: String,

    #[arg(long, env = "HERMES_BIN", default_value = "/home/x/.local/bin/hermes")]
    hermes_bin: PathBuf,

    #[arg(long, env = "NOVA_ACTIVE_ROOT", default_value = "/adapt/novas/active")]
    active_root: PathBuf,

    #[arg(
        long,
        env = "HERMES_PROFILE_ROOT",
        default_value = "/home/x/.hermes/profiles"
    )]
    profile_root: PathBuf,

    #[arg(long, env = "HERMES_TURN_TIMEOUT_SECONDS", default_value_t = 300)]
    turn_timeout_seconds: u64,

    #[arg(long, env = "HERMES_MAX_TURNS", default_value_t = 20)]
    max_turns: u32,

    #[arg(long, env = "NOVA_MAX_QUEUE_DEPTH", default_value_t = 8)]
    max_queue_depth: usize,

    #[arg(long, env = "HERMES_MODEL")]
    model: Option<String>,

    #[arg(long, env = "HERMES_PROVIDER")]
    provider: Option<String>,

    #[arg(long, env = "HERMES_SESSION_MODE", default_value = "latest")]
    session_mode: String,
}

#[derive(Debug, Clone)]
struct Subjects {
    direct: String,
    meet: String,
    ping: String,
    logs: String,
}

impl Subjects {
    fn from_args(args: &Args) -> Self {
        let native_root = format!("{}.{}.native", args.subject_prefix, args.agent);
        Self {
            direct: args
                .direct_subject
                .clone()
                .unwrap_or_else(|| native_root.clone()),
            meet: args
                .meet_subject
                .clone()
                .unwrap_or_else(|| format!("{}.meet", native_root)),
            ping: args
                .ping_subject
                .clone()
                .unwrap_or_else(|| format!("{}.ping", native_root)),
            logs: format!("{}.logs.{}", args.subject_prefix, args.agent),
        }
    }
}

#[derive(Debug, Clone, Deserialize)]
struct NatsEnvelope {
    id: Option<String>,
    from: Option<String>,
    message: Option<String>,
    reply_to: Option<String>,
    timestamp: Option<f64>,
}

#[derive(Debug, Clone)]
struct BridgeWork {
    event_id: String,
    sender: String,
    channel: Channel,
    message: String,
    reply_to: Option<String>,
    received_timestamp: Option<f64>,
}

#[derive(Debug, Clone, Copy, Serialize)]
#[serde(rename_all = "lowercase")]
enum Channel {
    Direct,
    Meet,
}

#[derive(Debug, Serialize)]
struct ReplyChunk<'a> {
    chunk: &'a str,
    #[serde(rename = "final")]
    final_chunk: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<&'a str>,
}

#[derive(Debug, Serialize)]
struct TraceEvent<'a> {
    from: &'a str,
    agent: &'a str,
    event_id: &'a str,
    stage: &'a str,
    channel: Channel,
    sender: &'a str,
    reply_to: bool,
    queue_depth: Option<usize>,
    received_timestamp: Option<f64>,
    timestamp: u64,
}

#[derive(Debug, Error)]
enum BridgeError {
    #[error("message envelope was not valid JSON: {0}")]
    InvalidEnvelope(#[from] serde_json::Error),
    #[error("message field is empty")]
    EmptyMessage,
    #[error("Hermes profile {agent} timed out after {seconds}s")]
    HermesTimeout { agent: String, seconds: u64 },
    #[error("Hermes profile {agent} exited {code}: {stderr}")]
    HermesFailed {
        agent: String,
        code: i32,
        stderr: String,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter("info,nova_hermes_nats_bridge=debug")
        .with_target(false)
        .init();

    let args = Args::parse();
    let subjects = Subjects::from_args(&args);
    let client = connect_nats(&args).await?;

    info!(
        agent = %args.agent,
        direct = %subjects.direct,
        meet = %subjects.meet,
        ping = %subjects.ping,
        "Rust Hermes NATS bridge starting"
    );

    let (work_tx, work_rx) = mpsc::channel::<BridgeWork>(args.max_queue_depth);

    subscribe_work(
        client.clone(),
        subjects.direct.clone(),
        Channel::Direct,
        work_tx.clone(),
        subjects.clone(),
        args.clone(),
    )
    .await?;
    subscribe_work(
        client.clone(),
        subjects.meet.clone(),
        Channel::Meet,
        work_tx,
        subjects.clone(),
        args.clone(),
    )
    .await?;
    subscribe_ping(client.clone(), subjects.ping.clone(), args.agent.clone()).await?;

    let worker_client = client.clone();
    let worker_subjects = subjects.clone();
    let worker_args = args.clone();
    tokio::spawn(async move {
        run_worker(worker_client, worker_subjects, worker_args, work_rx).await;
    });

    tokio::signal::ctrl_c().await?;
    info!("shutdown requested");
    client.drain().await?;
    Ok(())
}

async fn connect_nats(args: &Args) -> Result<Client> {
    match (&args.nats_user, &args.nats_password) {
        (Some(user), Some(password)) => {
            ConnectOptions::with_user_and_password(user.clone(), password.clone())
                .connect(args.nats_url.as_str())
                .await
                .context("failed to connect to NATS with user/password")
        }
        _ => async_nats::connect(args.nats_url.as_str())
            .await
            .context("failed to connect to NATS"),
    }
}

async fn subscribe_work(
    client: Client,
    subject: String,
    channel: Channel,
    work_tx: mpsc::Sender<BridgeWork>,
    subjects: Subjects,
    args: Args,
) -> Result<()> {
    let subscriber = client
        .subscribe(subject.clone())
        .await
        .with_context(|| format!("failed to subscribe to {subject}"))?;
    tokio::spawn(async move {
        if let Err(error) =
            run_work_subscription(client, subscriber, channel, work_tx, subjects, args).await
        {
            error!(%subject, error = %error, "work subscription exited");
        }
    });
    Ok(())
}

async fn run_work_subscription(
    client: Client,
    mut subscriber: Subscriber,
    channel: Channel,
    work_tx: mpsc::Sender<BridgeWork>,
    subjects: Subjects,
    args: Args,
) -> Result<()> {
    while let Some(message) = subscriber.next().await {
        let work = match parse_work(message.payload.as_ref(), channel) {
            Ok(work) => work,
            Err(error) => {
                warn!(error = %error, "dropping invalid envelope");
                continue;
            }
        };

        let event_id = work.event_id.clone();
        let sender = work.sender.clone();
        let queue_depth = work_tx.capacity();
        if let Err(error) = publish_trace(
            &client,
            &subjects,
            &args,
            &work,
            "inbound",
            Some(args.max_queue_depth.saturating_sub(queue_depth)),
        )
        .await
        {
            warn!(error = %error, "failed to publish inbound trace");
        }

        match work_tx.try_send(work) {
            Ok(()) => {}
            Err(error) => {
                let failed = error.into_inner();
                warn!(event_id = %event_id, sender = %sender, "queue full");
                if let Some(reply_to) = failed.reply_to.as_deref() {
                    publish_error(&client, reply_to, "bridge queue is full; retry later").await?;
                }
            }
        }
    }
    Ok(())
}

fn parse_work(payload: &[u8], channel: Channel) -> Result<BridgeWork, BridgeError> {
    let envelope: NatsEnvelope = serde_json::from_slice(payload)?;
    let message = envelope.message.unwrap_or_default().trim().to_string();
    if message.is_empty() {
        return Err(BridgeError::EmptyMessage);
    }
    let sender = envelope.from.unwrap_or_else(|| "unknown".to_string());
    let event_id = envelope
        .id
        .unwrap_or_else(|| format!("rust-nats-{}-{}", sender, unix_timestamp()));
    Ok(BridgeWork {
        event_id,
        sender,
        channel,
        message,
        reply_to: envelope.reply_to,
        received_timestamp: envelope.timestamp,
    })
}

async fn subscribe_ping(client: Client, subject: String, agent: String) -> Result<()> {
    let mut subscriber = client
        .subscribe(subject.clone())
        .await
        .with_context(|| format!("failed to subscribe to {subject}"))?;
    tokio::spawn(async move {
        while let Some(message) = subscriber.next().await {
            if let Some(reply) = message.reply {
                let payload = format!("pong:{agent}:rust");
                if let Err(error) = client.publish(reply, payload.into()).await {
                    warn!(error = %error, "failed to publish ping response");
                }
            }
        }
    });
    Ok(())
}

async fn run_worker(
    client: Client,
    subjects: Subjects,
    args: Args,
    mut work_rx: mpsc::Receiver<BridgeWork>,
) {
    while let Some(work) = work_rx.recv().await {
        if let Err(error) = publish_trace(&client, &subjects, &args, &work, "started", None).await {
            warn!(error = %error, "failed to publish started trace");
        }

        let result = invoke_hermes(&args, &work).await;
        match result {
            Ok(reply) => {
                if let Some(reply_to) = work.reply_to.as_deref() {
                    if let Err(error) = publish_reply_words(&client, reply_to, &reply).await {
                        warn!(error = %error, "failed to publish reply");
                    }
                }
                if let Err(error) =
                    publish_trace(&client, &subjects, &args, &work, "completed", None).await
                {
                    warn!(error = %error, "failed to publish completed trace");
                }
            }
            Err(error) => {
                error!(event_id = %work.event_id, error = %error, "Hermes turn failed");
                if let Some(reply_to) = work.reply_to.as_deref() {
                    if let Err(publish_error_value) =
                        publish_error(&client, reply_to, "Hermes turn failed").await
                    {
                        warn!(error = %publish_error_value, "failed to publish turn error");
                    }
                }
                if let Err(trace_error) =
                    publish_trace(&client, &subjects, &args, &work, "error", None).await
                {
                    warn!(error = %trace_error, "failed to publish error trace");
                }
            }
        }
    }
}

async fn invoke_hermes(args: &Args, work: &BridgeWork) -> Result<String, BridgeError> {
    let prompt = format_prompt(args, work);
    let mut command = Command::new(&args.hermes_bin);
    command
        .arg("-p")
        .arg(&args.agent)
        .arg("chat")
        .args(session_args(args))
        .arg("-q")
        .arg(prompt)
        .arg("-Q")
        .arg("--yolo")
        .arg("--source")
        .arg("rust-nats")
        .arg("--max-turns")
        .arg(args.max_turns.to_string())
        .current_dir(agent_workdir(args))
        .kill_on_drop(true)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    if let Some(provider) = &args.provider {
        command.arg("--provider").arg(provider);
    }
    if let Some(model) = &args.model {
        command.arg("-m").arg(model);
    }

    let child = command.spawn().map_err(|error| BridgeError::HermesFailed {
        agent: args.agent.clone(),
        code: -1,
        stderr: error.to_string(),
    })?;
    let output = timeout(
        Duration::from_secs(args.turn_timeout_seconds),
        child.wait_with_output(),
    )
    .await
    .map_err(|_| BridgeError::HermesTimeout {
        agent: args.agent.clone(),
        seconds: args.turn_timeout_seconds,
    })?
    .map_err(|error| BridgeError::HermesFailed {
        agent: args.agent.clone(),
        code: -1,
        stderr: error.to_string(),
    })?;

    if !output.status.success() {
        return Err(BridgeError::HermesFailed {
            agent: args.agent.clone(),
            code: output.status.code().unwrap_or(-1),
            stderr: truncate(&String::from_utf8_lossy(&output.stderr), 500),
        });
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(clean_hermes_output(&stdout))
}

fn session_args(args: &Args) -> Vec<String> {
    match args.session_mode.trim().to_ascii_lowercase().as_str() {
        "fresh" | "none" | "off" => Vec::new(),
        "latest" | "continue" | "most-recent" => vec!["--continue".to_string()],
        value => vec!["--continue".to_string(), format!("rust-nats-{value}")],
    }
}

fn agent_workdir(args: &Args) -> PathBuf {
    let active = args.active_root.join(&args.agent);
    if active.exists() {
        return active;
    }
    let profile = args.profile_root.join(&args.agent);
    if profile.exists() {
        return profile;
    }
    PathBuf::from(".")
}

fn format_prompt(args: &Args, work: &BridgeWork) -> String {
    format!(
        "You are Hermes profile {agent}. This request came through the Rust Nova NATS bridge. \
Subject channel: {channel:?}. Sender: {sender}. Event ID: {event_id}. Message: {message}. \
Answer as yourself. Mention that this came through NATS when relevant.",
        agent = args.agent,
        channel = work.channel,
        sender = work.sender,
        event_id = work.event_id,
        message = work.message
    )
}

fn clean_hermes_output(output: &str) -> String {
    output
        .lines()
        .map(str::trim)
        .filter(|line| {
            !line.is_empty()
                && !line.starts_with("session_id:")
                && !line.starts_with("↻ Resumed session")
                && !line.starts_with("Resumed session")
                && !line.contains("No auxiliary LLM provider configured")
        })
        .collect::<Vec<_>>()
        .join(" ")
}

async fn publish_reply_words(client: &Client, reply_to: &str, text: &str) -> Result<()> {
    let words = text.split_whitespace().collect::<Vec<_>>();
    if words.is_empty() {
        let payload = ReplyChunk {
            chunk: "",
            final_chunk: true,
            error: None,
        };
        publish_json(client, reply_to, &payload).await?;
        return Ok(());
    }

    for chunk in words.chunks(7) {
        let text_chunk = format!("{} ", chunk.join(" "));
        let payload = ReplyChunk {
            chunk: text_chunk.as_str(),
            final_chunk: false,
            error: None,
        };
        publish_json(client, reply_to, &payload).await?;
    }

    let payload = ReplyChunk {
        chunk: "",
        final_chunk: true,
        error: None,
    };
    publish_json(client, reply_to, &payload).await?;
    Ok(())
}

async fn publish_error(client: &Client, reply_to: &str, message: &str) -> Result<()> {
    let payload = ReplyChunk {
        chunk: "",
        final_chunk: true,
        error: Some(message),
    };
    publish_json(client, reply_to, &payload).await
}

async fn publish_trace(
    client: &Client,
    subjects: &Subjects,
    args: &Args,
    work: &BridgeWork,
    stage: &str,
    queue_depth: Option<usize>,
) -> Result<()> {
    let event = TraceEvent {
        from: "nova-hermes-nats-bridge",
        agent: &args.agent,
        event_id: &work.event_id,
        stage,
        channel: work.channel,
        sender: &work.sender,
        reply_to: work.reply_to.is_some(),
        queue_depth,
        received_timestamp: work.received_timestamp,
        timestamp: unix_timestamp(),
    };
    publish_json(client, subjects.logs.as_str(), &event).await
}

async fn publish_json<T: Serialize>(client: &Client, subject: &str, value: &T) -> Result<()> {
    let payload = serde_json::to_vec(value)?;
    client.publish(subject.to_string(), payload.into()).await?;
    Ok(())
}

fn truncate(value: &str, max_chars: usize) -> String {
    value.chars().take(max_chars).collect()
}

fn unix_timestamp() -> u64 {
    match SystemTime::now().duration_since(UNIX_EPOCH) {
        Ok(duration) => duration.as_secs(),
        Err(_) => 0,
    }
}
