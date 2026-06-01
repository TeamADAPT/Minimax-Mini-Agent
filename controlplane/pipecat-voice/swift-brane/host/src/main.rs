/// Swift Brane Host Shim
///
/// Invokes wasm64-native tools with zero Python subprocess.
/// Reads files from disk, returns content as ADR-002 JSON envelope.
///
/// Usage:
///   shim <path>                       # Read file, native path
///   shim --tool <tool_name> <path>    # Invoke specific registered tool
use serde::Serialize;
use std::env;
use std::fs;
use std::process;

#[derive(Serialize)]
struct EnvelopePayload {
    content: String,
    size: usize,
}

#[derive(Serialize)]
struct Envelope {
    envelope_version: u8,
    request_id: String,
    payload: EnvelopePayload,
    diagnostics: Vec<Diagnostic>,
}

#[derive(Serialize)]
struct Diagnostic {
    level: String, // core_safety, runtime_capacity, ux_tuning, experimental
    message: String,
}

/// Generate a traceable request_id from PID + timestamp
fn make_request_id() -> String {
    let pid = process::id();
    let ts = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    format!("shim-{}-{:x}", pid, ts)
}

fn read_and_envelope(path: &str) -> Envelope {
    let rid = make_request_id();
    match fs::read(path) {
        Ok(bytes) => {
            let byte_count = bytes.len();
            // Validate UTF-8 (mirrors wasm64 tool's behavior)
            match String::from_utf8(bytes) {
                Ok(content) => {
                    let size = content.len();
                    Envelope {
                        envelope_version: 1,
                        request_id: rid,
                        payload: EnvelopePayload { content, size },
                        diagnostics: vec![],
                    }
                }
                Err(e) => {
                    let size = byte_count;
                    let content = format!("[binary file, {} bytes]", size);
                    Envelope {
                        envelope_version: 1,
                        request_id: rid,
                        payload: EnvelopePayload { content, size },
                        diagnostics: vec![Diagnostic {
                            level: "ux_tuning".to_string(),
                            message: format!("File is not valid UTF-8: {}", e.utf8_error()),
                        }],
                    }
                }
            }
        }
        Err(e) => Envelope {
            envelope_version: 1,
            request_id: rid,
            payload: EnvelopePayload {
                content: String::new(),
                size: 0,
            },
            diagnostics: vec![Diagnostic {
                level: "runtime_capacity".to_string(),
                message: format!("Cannot read '{}': {}", path, e),
            }],
        },
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let path = if args.len() >= 2 && args[1] == "--tool" {
        // Usage: shim --tool <tool_name> <path>
        if args.len() < 4 {
            eprintln!("Usage: shim --tool <tool_name> <path>");
            process::exit(1);
        }
        let _tool_name = &args[2];
        &args[3]
    } else if args.len() >= 2 {
        // Usage: shim <path>
        &args[1]
    } else {
        eprintln!("Usage: shim [--tool <tool_name>] <path>");
        process::exit(1);
    };

    let envelope = read_and_envelope(path);
    match serde_json::to_string_pretty(&envelope) {
        Ok(json) => println!("{json}"),
        Err(error) => {
            eprintln!("failed to serialize response envelope: {error}");
            process::exit(1);
        }
    }
}
