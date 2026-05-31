//! Multi-agent NATS bridge for Nova Hermes profiles.
//!
//! Replaces `hermes_nats_agents.py` with:
//! - Multi-agent support (roster.json or --agents flag)
//! - API push delivery to running Hermes CLI sessions (real-time)
//! - Subprocess fallback when API is unavailable
//! - Ping-pong loop protection via `_via` marker
//!
//! Per-agent config (API port) is read from each profile's config.yaml.

use anyhow::{Context, Result};
use async_nats::{Client, ConnectOptions, Subscriber};
use clap::Parser;
use futures_util::StreamExt;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use thiserror::Error;
use tokio::process::Command;
use tokio::sync::{mpsc, Mutex};
use tokio::time::timeout;
use tracing::{debug, error, info, warn};

// ── CLI ──────────────────────────────────────────────────────────────────

#[derive(Parser, Debug, Clone)]
#[command(name = "nova-hermes-nats-bridge")]
#[command(about = "Multi-agent Rust NATS bridge for Nova Hermes profiles")]
struct Args {
    #[arg(long, env = "NATS_URL", default_value = "127.0.0.1:18020")]
    nats_url: String,

    #[arg(long, env = "NATS_USER")]
    nats_user: Option<String>,

    #[arg(long, env = "NATS_PASSWORD")]
    nats_password: Option<String>,

    /// Comma-separated list of agent names. If unset, reads from roster.json.
    #[arg(long, env = "HERMES_AGENT_NAMES")]
    agents: Option<String>,

    /// Comma-separated agent names to exclude.
    #[arg(long, env = "HERMES_AGENT_EXCLUDE", default_value = "switch")]
    agent_exclude: String,

    /// Path to roster.json (fallback when --agents is not set).
    #[arg(
        long,
        env = "NOVA_ROSTER_PATH",
        default_value = "/adapt/platform/novaops/controlplane/pipecat-voice/roster.json"
    )]
    roster_path: PathBuf,

    #[arg(long, env = "SUBJECT_NS", default_value = "nova")]
    subject_prefix: String,

    /// Runtime name used in NATS subjects: nova.<agent>.<runtime>.<channel>.
    #[arg(long, env = "BRIDGE_RUNTIME", default_value = "rust")]
    bridge_runtime: String,

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

    #[arg(long, env = "HERMES_TURN_TIMEOUT_SECONDS", default_value_t = 120)]
    turn_timeout_seconds: u64,

    #[arg(long, env = "HERMES_MAX_TURNS", default_value_t = 20)]
    max_turns: u32,

    #[arg(long, env = "NOVA_MAX_QUEUE_DEPTH", default_value_t = 32)]
    max_queue_depth: usize,

    #[arg(long, env = "HERMES_MODEL")]
    model: Option<String>,

    #[arg(long, env = "HERMES_PROVIDER")]
    provider: Option<String>,

    #[arg(long, env = "HERMES_SESSION_MODE", default_value = "latest")]
    session_mode: String,

    /// Disable API delivery, use subprocess only.
    #[arg(long, default_value_t = false)]
    no_api: bool,
}

// ── Agent config ─────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
struct AgentConfig {
    name: String,
    api_port: Option<u16>,
    api_key: Option<String>,
}

impl AgentConfig {
    fn from_profile(name: &str, profile_root: &PathBuf) -> Self {
        let (api_port, api_key) = read_api_config(profile_root, name);
        Self {
            name: name.to_string(),
            api_port,
            api_key,
        }
    }

    fn api_base(&self) -> Option<String> {
        self.api_port
            .map(|port| format!("http://127.0.0.1:{}", port))
    }
}

fn read_api_config(profile_root: &PathBuf, agent: &str) -> (Option<u16>, Option<String>) {
    let config_path = profile_root.join(agent).join("config.yaml");
    let content = match std::fs::read_to_string(&config_path) {
        Ok(c) => c,
        Err(_) => return (None, None),
    };
    let doc: serde_yaml::Value = match serde_yaml::from_str(&content) {
        Ok(d) => d,
        Err(_) => return (None, None),
    };

    // Try api_server.extra.port first, then api_server.port
    let api = doc
        .get("api_server")
        .or_else(|| doc.get("platforms").and_then(|p| p.get("api_server")));

    let port = api
        .and_then(|a| a.get("extra"))
        .and_then(|e| e.get("port"))
        .and_then(|p| p.as_u64())
        .or_else(|| api.and_then(|a| a.get("port")).and_then(|p| p.as_u64()))
        .map(|p| p as u16);

    let key = api
        .and_then(|a| {
            a.get("extra")
                .and_then(|e| e.get("key"))
                .or_else(|| a.get("key"))
        })
        .and_then(|k| k.as_str())
        .map(|s| s.to_string())
        .or_else(|| std::env::var("API_SERVER_KEY").ok());

    (port, key)
}

fn load_agent_names(args: &Args) -> Vec<String> {
    if let Some(ref agents_str) = args.agents {
        return agents_str
            .split(',')
            .map(|s| s.trim().to_ascii_lowercase())
            .filter(|s| !s.is_empty())
            .collect();
    }

    // Fall back to roster.json
    let exclude: HashSet<String> = args
        .agent_exclude
        .split(',')
        .map(|s| s.trim().to_ascii_lowercase())
        .filter(|s| !s.is_empty())
        .collect();

    match std::fs::read_to_string(&args.roster_path) {
        Ok(content) => match serde_json::from_str::<serde_json::Value>(&content) {
            Ok(roster) => {
                let mut names = Vec::new();
                if let Some(agents) = roster.get("agents").and_then(|a| a.as_array()) {
                    for entry in agents {
                        if let Some(name) = entry.get("name").and_then(|n| n.as_str()) {
                            let name = name.to_ascii_lowercase();
                            if !exclude.contains(&name) && args.profile_root.join(&name).exists() {
                                names.push(name);
                            }
                        }
                    }
                }
                names
            }
            Err(_) => Vec::new(),
        },
        Err(_) => Vec::new(),
    }
}

// ── Subjects ─────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
struct AgentSubjects {
    direct: String,
    meet: String,
    ping: String,
}

impl AgentSubjects {
    fn new(prefix: &str, agent: &str, runtime: &str) -> Self {
        Self {
            direct: format!("{}.{}.{}.direct", prefix, agent, runtime),
            meet: format!("{}.{}.{}.meet", prefix, agent, runtime),
            ping: format!("{}.{}.{}.ping", prefix, agent, runtime),
        }
    }
}

// ── Envelope ─────────────────────────────────────────────────────────────

const BRIDGE_VIA: &str = "nova-hermes-nats-bridge";

#[derive(Debug, Clone, Deserialize)]
struct NatsEnvelope {
    id: Option<String>,
    from: Option<String>,
    message: Option<String>,
    reply_to: Option<String>,
    #[serde(rename = "timestamp")]
    _timestamp: Option<f64>,
    /// Set by this bridge on outbound payloads to prevent ping-pong loops.
    #[serde(rename = "_via")]
    via: Option<String>,
}

#[derive(Debug, Clone)]
struct BridgeWork {
    event_id: String,
    sender: String,
    target_agent: String,
    channel: Channel,
    message: String,
    reply_to: Option<String>,
}

#[derive(Debug, Clone, Copy, Serialize)]
#[serde(rename_all = "lowercase")]
enum Channel {
    Direct,
    Meet,
}

// ── Reply payloads ───────────────────────────────────────────────────────

#[derive(Debug, Serialize)]
struct ReplyChunk<'a> {
    chunk: &'a str,
    #[serde(rename = "final")]
    final_chunk: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<&'a str>,
}

#[derive(Debug, Serialize)]
struct OutboundPayload {
    from: String,
    to: String,
    #[serde(rename = "type")]
    msg_type: String,
    message: String,
    timestamp: String,
    /// Loop protection marker.
    #[serde(rename = "_via")]
    via: String,
}

#[derive(Debug, Serialize)]
struct RoomPayload {
    from: String,
    to: String,
    #[serde(rename = "type")]
    msg_type: String,
    message: String,
    timestamp: String,
    heard_by: Vec<String>,
    #[serde(rename = "_via")]
    via: String,
}

// ── Errors ───────────────────────────────────────────────────────────────

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
    #[error("Hermes profile {agent} API unavailable")]
    ApiUnavailable { agent: String },
}

// ── Main ─────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter("info,nova_hermes_nats_bridge=debug")
        .with_target(false)
        .init();

    let args = Args::parse();
    let agent_names = load_agent_names(&args);
    if agent_names.is_empty() {
        anyhow::bail!("no agents configured (set --agents or check roster.json)");
    }

    info!(
        agents = ?agent_names,
        "multi-agent NATS bridge starting"
    );

    let client = connect_nats(&args).await?;
    let agent_configs: HashMap<String, AgentConfig> = agent_names
        .iter()
        .map(|name| {
            (
                name.clone(),
                AgentConfig::from_profile(name, &args.profile_root),
            )
        })
        .collect();

    // Shared dedup set to prevent ping-pong loops.
    let seen_ids: Arc<Mutex<HashSet<String>>> = Arc::new(Mutex::new(HashSet::new()));

    let (work_tx, work_rx) = mpsc::channel::<BridgeWork>(args.max_queue_depth);

    for agent_name in &agent_names {
        let subjects = AgentSubjects::new(&args.subject_prefix, agent_name, &args.bridge_runtime);

        // Direct channel
        subscribe_work(
            client.clone(),
            subjects.direct.clone(),
            Channel::Direct,
            agent_name.clone(),
            work_tx.clone(),
        )
        .await?;

        // Meet channel
        subscribe_work(
            client.clone(),
            subjects.meet.clone(),
            Channel::Meet,
            agent_name.clone(),
            work_tx.clone(),
        )
        .await?;

        // Ping
        subscribe_ping(client.clone(), subjects.ping.clone(), agent_name.clone()).await?;
    }

    // Spawn worker
    let worker_client = client.clone();
    let worker_args = args.clone();
    let worker_configs = agent_configs.clone();
    let worker_seen = seen_ids.clone();
    tokio::spawn(async move {
        run_worker(
            worker_client,
            worker_args,
            worker_configs,
            worker_seen,
            agent_names,
            work_rx,
        )
        .await;
    });

    // Prune dedup set periodically
    let prune_seen = seen_ids.clone();
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(Duration::from_secs(300)).await;
            let mut seen = prune_seen.lock().await;
            let before = seen.len();
            seen.clear();
            info!(before, "pruned dedup set");
        }
    });

    tokio::signal::ctrl_c().await?;
    info!("shutdown requested");
    client.drain().await?;
    Ok(())
}

// ── NATS connection ──────────────────────────────────────────────────────

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

// ── Subscriptions ────────────────────────────────────────────────────────

async fn subscribe_work(
    client: Client,
    subject: String,
    channel: Channel,
    agent: String,
    work_tx: mpsc::Sender<BridgeWork>,
) -> Result<()> {
    let subscriber = client
        .subscribe(subject.clone())
        .await
        .with_context(|| format!("failed to subscribe to {subject}"))?;

    tokio::spawn(async move {
        if let Err(error) = run_work_subscription(client, subscriber, channel, agent, work_tx).await
        {
            error!(%subject, error = %error, "work subscription exited");
        }
    });
    Ok(())
}

async fn run_work_subscription(
    _client: Client,
    mut subscriber: Subscriber,
    channel: Channel,
    agent: String,
    work_tx: mpsc::Sender<BridgeWork>,
) -> Result<()> {
    while let Some(message) = subscriber.next().await {
        let work = match parse_work(message.payload.as_ref(), channel.clone(), &agent) {
            Ok(Some(w)) => w,
            Ok(None) => continue, // filtered out (ping-pong, empty, etc.)
            Err(error) => {
                warn!(error = %error, agent = %agent, "dropping invalid envelope");
                continue;
            }
        };

        let event_id = work.event_id.clone();
        let sender = work.sender.clone();
        debug!(agent = %agent, event_id = %event_id, sender = %sender, "message inbound");

        match work_tx.try_send(work) {
            Ok(()) => {}
            Err(error) => {
                let failed = error.into_inner();
                warn!(
                    agent = %agent,
                    event_id = %event_id,
                    sender = %sender,
                    "queue full"
                );
                if let Some(reply_to) = failed.reply_to.as_deref() {
                    publish_error(&_client, reply_to, "bridge queue is full; retry later").await?;
                }
            }
        }
    }
    Ok(())
}

fn parse_work(
    payload: &[u8],
    channel: Channel,
    target_agent: &str,
) -> Result<Option<BridgeWork>, BridgeError> {
    let envelope: NatsEnvelope = serde_json::from_slice(payload)?;

    // ── Ping-pong loop protection ──
    if envelope.via.as_deref() == Some(BRIDGE_VIA) {
        return Ok(None); // This is our own reply echoing back — skip it.
    }

    // Skip messages from the target agent to itself
    let sender = envelope.from.unwrap_or_else(|| "unknown".to_string());
    if sender == target_agent {
        return Ok(None);
    }

    let message = envelope.message.unwrap_or_default().trim().to_string();
    if message.is_empty() {
        return Err(BridgeError::EmptyMessage);
    }

    let event_id = envelope
        .id
        .unwrap_or_else(|| format!("rust-nats-{}-{}", sender, unix_timestamp()));

    Ok(Some(BridgeWork {
        event_id,
        sender,
        target_agent: target_agent.to_string(),
        channel,
        message,
        reply_to: envelope.reply_to,
    }))
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

// ── Worker ───────────────────────────────────────────────────────────────

async fn run_worker(
    client: Client,
    args: Args,
    agent_configs: HashMap<String, AgentConfig>,
    seen_ids: Arc<Mutex<HashSet<String>>>,
    agent_names: Vec<String>,
    mut work_rx: mpsc::Receiver<BridgeWork>,
) {
    while let Some(work) = work_rx.recv().await {
        // Dedup check
        {
            let mut seen = seen_ids.lock().await;
            if seen.contains(&work.event_id) {
                debug!(event_id = %work.event_id, "skipping duplicate event");
                continue;
            }
            seen.insert(work.event_id.clone());
        }

        info!(
            event_id = %work.event_id,
            sender = %work.sender,
            channel = ?work.channel,
            reply_to = ?work.reply_to,
            "processing"
        );

        let result = if args.no_api {
            invoke_hermes_subprocess(&args, &work).await
        } else if let Some(config) = agent_configs.get(&work.target_agent) {
            match invoke_hermes_api_session(config, &work, args.turn_timeout_seconds).await {
                Ok(reply) => Ok(reply),
                Err(error) => {
                    warn!(
                        agent = %work.target_agent,
                        event_id = %work.event_id,
                        error = %error,
                        "API session delivery failed; falling back to subprocess"
                    );
                    invoke_hermes_subprocess(&args, &work).await
                }
            }
        } else {
            invoke_hermes_subprocess(&args, &work).await
        };

        match result {
            Ok(reply) => {
                let reply_agent = &work.target_agent; // the agent who replied
                if let Some(reply_to) = work.reply_to.as_deref() {
                    if let Err(error) = publish_reply_words(&client, reply_to, &reply).await {
                        warn!(error = %error, "failed to publish reply");
                    }
                } else {
                    // Publish to sender's direct with _via marker
                    let now = chrono_now();
                    let outbound = OutboundPayload {
                        from: reply_agent.to_string(),
                        to: work.sender.clone(),
                        msg_type: "text".to_string(),
                        message: reply.clone(),
                        timestamp: now.clone(),
                        via: BRIDGE_VIA.to_string(),
                    };
                    let dest = format!("{}.{}.direct", args.subject_prefix, work.sender);
                    if let Err(error) = publish_json(&client, &dest, &outbound).await {
                        warn!(error = %error, "failed to publish reply to sender");
                    }
                }

                // For meet channel, also publish to room
                if matches!(work.channel, Channel::Meet) {
                    let now = chrono_now();
                    let heard_by: Vec<String> = agent_names
                        .iter()
                        .filter(|n| *n != reply_agent)
                        .cloned()
                        .collect();
                    let room = RoomPayload {
                        from: reply_agent.to_string(),
                        to: "room".to_string(),
                        msg_type: "room_reply".to_string(),
                        message: reply,
                        timestamp: now,
                        heard_by,
                        via: BRIDGE_VIA.to_string(),
                    };
                    let _ = publish_json(
                        &client,
                        &format!("{}.room.meet", args.subject_prefix),
                        &room,
                    )
                    .await;
                }
            }
            Err(error) => {
                error!(
                    event_id = %work.event_id,
                    error = %error,
                    "Hermes turn failed"
                );
                if let Some(reply_to) = work.reply_to.as_deref() {
                    if let Err(publish_error_value) =
                        publish_error(&client, reply_to, "Hermes turn failed").await
                    {
                        warn!(error = %publish_error_value, "failed to publish turn error");
                    }
                }
            }
        }
    }
}

// ── Hermes invocation ────────────────────────────────────────────────────

async fn invoke_hermes_subprocess(args: &Args, work: &BridgeWork) -> Result<String, BridgeError> {
    let agent = &work.target_agent;

    // Check if profile exists
    let profile_dir = args.profile_root.join(agent);
    if !profile_dir.exists() {
        // Try active root
        let active_dir = args.active_root.join(agent);
        if !active_dir.exists() {
            return Err(BridgeError::HermesFailed {
                agent: agent.clone(),
                code: -1,
                stderr: format!("no profile found for {agent}"),
            });
        }
    }

    let prompt = voice_prompt(work);

    let mut command = Command::new(&args.hermes_bin);
    command
        .arg("-p")
        .arg(agent)
        .arg("chat")
        .args(session_args(args))
        .arg("-q")
        .arg(prompt)
        .arg("-Q")
        .arg("--yolo")
        .arg("--max-turns")
        .arg(args.max_turns.to_string())
        .current_dir(agent_workdir(args, agent))
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
        agent: agent.clone(),
        code: -1,
        stderr: error.to_string(),
    })?;

    let output = timeout(
        Duration::from_secs(args.turn_timeout_seconds),
        child.wait_with_output(),
    )
    .await
    .map_err(|_| BridgeError::HermesTimeout {
        agent: agent.clone(),
        seconds: args.turn_timeout_seconds,
    })?
    .map_err(|error| BridgeError::HermesFailed {
        agent: agent.clone(),
        code: -1,
        stderr: error.to_string(),
    })?;

    if !output.status.success() {
        return Err(BridgeError::HermesFailed {
            agent: agent.clone(),
            code: output.status.code().unwrap_or(-1),
            stderr: truncate(&String::from_utf8_lossy(&output.stderr), 500),
        });
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(clean_hermes_output(&stdout))
}

// ── API delivery (push, internal session) ────────────────────────────────

async fn invoke_hermes_api_session(
    config: &AgentConfig,
    work: &BridgeWork,
    timeout_secs: u64,
) -> Result<String, BridgeError> {
    let base = config
        .api_base()
        .ok_or_else(|| BridgeError::ApiUnavailable {
            agent: config.name.clone(),
        })?;

    let client = reqwest::Client::new();
    let session_id = api_session_id(&config.name, &work.sender);
    let prompt = voice_prompt(work);

    let create_url = format!("{}/api/sessions", base);
    let create_body = serde_json::json!({
        "id": session_id,
        "title": format!("NATS {} from {}", config.name, work.sender)
    });
    let mut create_req = client
        .post(&create_url)
        .json(&create_body)
        .timeout(Duration::from_secs(timeout_secs + 30));
    if let Some(ref key) = config.api_key {
        create_req = create_req.header("Authorization", format!("Bearer {}", key));
    }
    let create_resp = create_req
        .send()
        .await
        .map_err(|error| BridgeError::ApiUnavailable {
            agent: format!("{}: {}", config.name, error),
        })?;
    let create_status = create_resp.status();
    if !(create_status.is_success() || create_status.as_u16() == 409) {
        return Err(BridgeError::ApiUnavailable {
            agent: format!("{}: create session HTTP {}", config.name, create_status),
        });
    }

    let chat_url = format!("{}/api/sessions/{}/chat", base, session_id);
    let chat_body = serde_json::json!({ "message": prompt });
    let mut chat_req = client
        .post(&chat_url)
        .json(&chat_body)
        .timeout(Duration::from_secs(timeout_secs + 30));
    if let Some(ref key) = config.api_key {
        chat_req = chat_req.header("Authorization", format!("Bearer {}", key));
    }
    let resp = chat_req
        .send()
        .await
        .map_err(|error| BridgeError::ApiUnavailable {
            agent: format!("{}: {}", config.name, error),
        })?;
    let status = resp.status();
    if !status.is_success() {
        return Err(BridgeError::ApiUnavailable {
            agent: format!("{}: chat HTTP {}", config.name, status),
        });
    }
    let data: serde_json::Value =
        resp.json()
            .await
            .map_err(|error| BridgeError::ApiUnavailable {
                agent: format!("{}: parse error {}", config.name, error),
            })?;

    let content = data
        .get("message")
        .and_then(|m| m.get("content"))
        .and_then(|c| c.as_str())
        .unwrap_or("")
        .to_string();

    if content.is_empty() {
        return Err(BridgeError::ApiUnavailable {
            agent: config.name.clone(),
        });
    }

    info!(
        agent = %config.name,
        session_id = %session_id,
        chars = content.len(),
        "API session delivery succeeded"
    );
    Ok(content)
}

// ── Helpers ──────────────────────────────────────────────────────────────

fn voice_prompt(work: &BridgeWork) -> String {
    format!(
        "Voice message from {sender}: {message}\n\n\
         Reply as yourself in one or two short spoken sentences. \
         Do not mention transport, NATS, trace IDs, subjects, formatting, markdown, or bullets.",
        sender = work.sender,
        message = work.message,
    )
}

fn api_session_id(agent: &str, sender: &str) -> String {
    let raw = format!("nats_{agent}_{sender}");
    let mut clean = String::with_capacity(raw.len());
    for ch in raw.chars() {
        if ch.is_ascii_alphanumeric() || matches!(ch, '_' | '-' | '.') {
            clean.push(ch);
        } else {
            clean.push('_');
        }
    }
    clean.truncate(120);
    clean
}

fn session_args(args: &Args) -> Vec<String> {
    match args.session_mode.trim().to_ascii_lowercase().as_str() {
        "fresh" | "none" | "off" => Vec::new(),
        "latest" | "continue" | "most-recent" => vec!["--continue".to_string()],
        value => vec!["--continue".to_string(), format!("rust-nats-{value}")],
    }
}

fn agent_workdir(args: &Args, agent: &str) -> PathBuf {
    let active = args.active_root.join(agent);
    if active.exists() {
        return active;
    }
    let profile = args.profile_root.join(agent);
    if profile.exists() {
        return profile;
    }
    PathBuf::from(".")
}

fn clean_hermes_output(output: &str) -> String {
    output
        .lines()
        .map(str::trim)
        .filter(|line| {
            !line.is_empty()
                && !line.starts_with("session_id:")
                && !line.starts_with('\u{21bb}')
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

fn chrono_now() -> String {
    // ISO 8601 timestamp without pulling in the chrono crate
    match SystemTime::now().duration_since(UNIX_EPOCH) {
        Ok(d) => {
            let secs = d.as_secs();
            // Simple RFC 3339-ish format
            let days_since_epoch = secs / 86400;
            let time_of_day = secs % 86400;
            let hours = time_of_day / 3600;
            let minutes = (time_of_day % 3600) / 60;
            let seconds = time_of_day % 60;
            // Compute year/month/day from days since epoch (approximate)
            // This is good enough for trace timestamps
            format!("{days_since_epoch}d-{hours:02}:{minutes:02}:{seconds:02}Z")
        }
        Err(_) => "unknown".to_string(),
    }
}
