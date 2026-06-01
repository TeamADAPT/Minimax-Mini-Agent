/// Swift Brane Agent — ADR-002 Envelope Shim + Host Function Provider
///
/// This binary implements the NEXUS-side adapter for wasm64 tools.
/// It is the sandbox boundary (L010): all I/O passes through here.
///
/// Modes:
///   stdin mode:       cat envelope.json | swift-brane-agent
///   CLI arg mode:     swift-brane-agent --tool file-read /etc/hostname
///   envelope mode:    swift-brane-agent --envelope "$(cat envelope.json)"
///   NATS listener:    swift-brane-agent --listen
///
/// The agent also implements the host function interface:
///   - The wasm64 tool exports `file_read(path_ptr, path_len)` for validation
///   - The agent provides `host_file_read(path) -> bytes` for actual I/O
///   - The tool NEVER performs I/O itself (L010)
mod envelope;
mod host_functions;
mod tool_interface;

use anyhow::{Context, Result};
use futures_util::StreamExt;
use std::env;
use std::io::Read;
use std::process;

use envelope::{DiagnosticLevel, Envelope};

const DEFAULT_NATS_URL: &str = "nats://127.0.0.1:18020";
const DEFAULT_LISTEN_SUBJECT: &str = "nova.crew.swift.invoke";
const DEFAULT_QUEUE_GROUP: &str = "swift-brane-workers";

fn process_path(path: &str, request_id: &str) -> String {
    // Step 1: Validate path using the wasm64 tool's logic (pure, no I/O)
    let validation_status = host_functions::validate_path_with_tool(path);
    if validation_status != tool_interface::FILE_READ_OK {
        let msg = match validation_status {
            tool_interface::FILE_READ_ERR_NULL => "Path is null or empty",
            tool_interface::FILE_READ_ERR_UTF8 => "Path contains invalid characters",
            _ => "Path validation failed",
        };
        let envelope = Envelope::error(
            request_id.to_string(),
            DiagnosticLevel::RuntimeCapacity,
            msg.to_string(),
        );
        return envelope.to_json();
    }

    // Step 2: Perform actual I/O via host function (L010 gate)
    match host_functions::host_file_read(path) {
        host_functions::HostResult::Success(bytes) => {
            // Validate content is valid UTF-8
            let byte_count = bytes.len();
            match String::from_utf8(bytes) {
                Ok(content) => Envelope::success(request_id.to_string(), content).to_json(),
                Err(e) => {
                    let size = byte_count;
                    let env = Envelope {
                        envelope_version: 1,
                        request_id: request_id.to_string(),
                        payload: serde_json::json!({
                            "content": format!("[binary file, {} bytes]", size),
                            "size": size
                        }),
                        diagnostics: vec![envelope::Diagnostic {
                            level: DiagnosticLevel::UxTuning,
                            message: format!("File is not valid UTF-8: {}", e.utf8_error()),
                        }],
                    };
                    env.to_json()
                }
            }
        }
        host_functions::HostResult::NotFound => Envelope::error(
            request_id.to_string(),
            DiagnosticLevel::RuntimeCapacity,
            format!("File not found: {}", path),
        )
        .to_json(),
        host_functions::HostResult::IoError(msg) => Envelope::error(
            request_id.to_string(),
            DiagnosticLevel::RuntimeCapacity,
            format!("I/O error reading '{}': {}", path, msg),
        )
        .to_json(),
    }
}

fn env_or_arg(args: &[String], flag: &str, env_key: &str, default_value: &str) -> String {
    args.windows(2)
        .find_map(|window| (window[0] == flag).then(|| window[1].clone()))
        .or_else(|| env::var(env_key).ok())
        .unwrap_or_else(|| default_value.to_string())
}

fn redacted_nats_url(url: &str) -> String {
    let without_scheme = url.split_once("://").map_or(url, |(_, rest)| rest);
    let host = without_scheme
        .rsplit_once('@')
        .map_or(without_scheme, |(_, rest)| rest);
    format!("nats://{host}")
}

fn nats_connect_options() -> async_nats::ConnectOptions {
    match (env::var("NATS_USER"), env::var("NATS_PASSWORD")) {
        (Ok(user), Ok(password)) if !user.is_empty() && !password.is_empty() => {
            async_nats::ConnectOptions::with_user_and_password(user, password)
        }
        _ => async_nats::ConnectOptions::new(),
    }
}

async fn run_listener(args: &[String]) -> Result<()> {
    let nats_url = env_or_arg(args, "--nats-url", "NATS_URL", DEFAULT_NATS_URL);
    let subject = env_or_arg(
        args,
        "--subject",
        "SWIFT_BRANE_SUBJECT",
        DEFAULT_LISTEN_SUBJECT,
    );
    let queue = env_or_arg(args, "--queue", "SWIFT_BRANE_QUEUE", DEFAULT_QUEUE_GROUP);

    eprintln!(
        "swift-brane-agent listening subject={} queue={} server={}",
        subject,
        queue,
        redacted_nats_url(&nats_url)
    );

    let client = nats_connect_options()
        .connect(nats_url)
        .await
        .context("failed to connect to NATS")?;
    let mut subscriber = client
        .queue_subscribe(subject.clone(), queue)
        .await
        .with_context(|| format!("failed to subscribe to {subject}"))?;

    while let Some(message) = subscriber.next().await {
        let request_id = envelope::make_request_id();
        let response = match std::str::from_utf8(&message.payload) {
            Ok(payload) => match Envelope::from_json(payload) {
                Ok(envelope) => {
                    let path = envelope
                        .payload
                        .get("path")
                        .and_then(|value| value.as_str())
                        .unwrap_or("");
                    process_path(path, &envelope.request_id)
                }
                Err(error) => {
                    Envelope::error(request_id, DiagnosticLevel::RuntimeCapacity, error).to_json()
                }
            },
            Err(error) => Envelope::error(
                request_id,
                DiagnosticLevel::RuntimeCapacity,
                format!("Payload is not valid UTF-8: {error}"),
            )
            .to_json(),
        };

        if let Some(reply) = message.reply {
            client
                .publish(reply, response.into())
                .await
                .context("failed to publish Swift Brane reply")?;
        } else {
            eprintln!("swift-brane-agent received request without reply subject");
        }
    }

    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();

    if args.len() >= 2 && args[1] == "--listen" {
        run_listener(&args).await?;
        return Ok(());
    }

    if args.len() >= 2 && args[1] == "--envelope" {
        // Envelope mode: read envelope JSON from stdin
        let mut input = String::new();
        if std::io::stdin().read_to_string(&mut input).is_err() {
            let envelope = Envelope::error(
                envelope::make_request_id(),
                DiagnosticLevel::RuntimeCapacity,
                "Failed to read stdin".to_string(),
            );
            println!("{}", envelope.to_json());
            process::exit(1);
        }

        let input = input.trim().to_string();
        match Envelope::from_json(&input) {
            Ok(env) => {
                let path = env
                    .payload
                    .get("path")
                    .and_then(|v| v.as_str())
                    .unwrap_or("");
                let rid = env.request_id;
                let result = process_path(path, &rid);
                println!("{}", result);
            }
            Err(e) => {
                let envelope = Envelope::error(
                    envelope::make_request_id(),
                    DiagnosticLevel::RuntimeCapacity,
                    e,
                );
                println!("{}", envelope.to_json());
                process::exit(1);
            }
        }
    } else if args.len() >= 2 {
        // CLI arg mode: swift-brane-agent <path>
        let path = &args[1];
        let rid = envelope::make_request_id();
        let result = process_path(path, &rid);
        println!("{}", result);
    } else {
        // No args: read stdin as raw path
        let mut input = String::new();
        if std::io::stdin().read_to_string(&mut input).is_err() || input.trim().is_empty() {
            eprintln!("Usage: swift-brane-agent <path>");
            eprintln!("       echo <path> | swift-brane-agent");
            process::exit(1);
        }
        let path = input.trim();
        let rid = envelope::make_request_id();
        let result = process_path(path, &rid);
        println!("{}", result);
    }
    Ok(())
}
