//! Probe provider text-to-speech endpoints without printing secrets.

use std::env;
use std::path::PathBuf;
use std::str::FromStr;
use std::time::Instant;

use clap::Parser;
use nova_voice_provider_core::{ProviderKind, XAI_TTS_URL};
use reqwest::header::{ACCEPT, AUTHORIZATION, CONTENT_TYPE};
use serde::{Deserialize, Serialize};

#[derive(Debug, Parser)]
#[command(name = "voice-provider-tts-probe")]
#[command(about = "Probe a Nova voice TTS provider without exposing credentials")]
struct Args {
    /// Provider id. Currently only xai has an HTTP TTS probe.
    #[arg(long, default_value = "xai")]
    provider: String,

    /// Text to synthesize.
    #[arg(long)]
    text: String,

    /// xAI voice id, for example eve.
    #[arg(long, default_value = "eve")]
    voice_id: String,

    /// BCP-47 language code.
    #[arg(long, default_value = "en")]
    language: String,

    /// Output MP3 path.
    #[arg(long)]
    out: PathBuf,

    /// Required guard for experimental providers.
    #[arg(long, default_value_t = false)]
    allow_experimental: bool,
}

#[derive(Debug, Serialize)]
struct ProbeReport {
    provider: ProviderKind,
    voice_id: String,
    language: String,
    output_path: String,
    bytes: u64,
    mime: String,
    latency_ms: u128,
}

#[derive(Debug, Serialize)]
struct XaiTtsRequest<'a> {
    text: &'a str,
    voice_id: &'a str,
    language: &'a str,
}

#[derive(Debug, Deserialize)]
struct ProviderErrorEnvelope {
    error: Option<ProviderErrorBody>,
}

#[derive(Debug, Deserialize)]
struct ProviderErrorBody {
    message: Option<String>,
    code: Option<String>,
    #[serde(rename = "type")]
    error_type: Option<String>,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    let provider = ProviderKind::from_str(&args.provider)?;
    match provider {
        ProviderKind::Xai => probe_xai(args).await?,
        ProviderKind::Deepgram => {
            return Err("deepgram HTTP TTS probe is not implemented in this binary".into());
        }
    }
    Ok(())
}

async fn probe_xai(args: Args) -> Result<(), Box<dyn std::error::Error>> {
    if !args.allow_experimental {
        return Err("xai TTS probe requires --allow-experimental".into());
    }

    let api_key = env::var("XAI_API_KEY")
        .map_err(|_| "XAI_API_KEY is required in the process environment")?;
    let request = XaiTtsRequest {
        text: args.text.as_str(),
        voice_id: args.voice_id.as_str(),
        language: args.language.as_str(),
    };

    let started = Instant::now();
    let response = reqwest::Client::new()
        .post(XAI_TTS_URL)
        .header(AUTHORIZATION, format!("Bearer {api_key}"))
        .header(CONTENT_TYPE, "application/json")
        .header(ACCEPT, "audio/mpeg, application/json")
        .json(&request)
        .send()
        .await?;
    let status = response.status();
    let body = response.bytes().await?;
    if !status.is_success() {
        return Err(provider_error(status.as_u16(), &body).into());
    }

    if let Some(parent) = args.out.parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::write(&args.out, &body)?;

    let report = ProbeReport {
        provider: ProviderKind::Xai,
        voice_id: args.voice_id,
        language: args.language,
        output_path: args.out.display().to_string(),
        bytes: body.len() as u64,
        mime: detect_mpeg(&body).to_string(),
        latency_ms: started.elapsed().as_millis(),
    };
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn provider_error(status: u16, body: &[u8]) -> String {
    let parsed = serde_json::from_slice::<ProviderErrorEnvelope>(body).ok();
    let safe_message = parsed
        .and_then(|envelope| envelope.error)
        .and_then(|error| {
            let mut parts = Vec::with_capacity(3);
            if let Some(code) = error.code {
                parts.push(format!("code={code}"));
            }
            if let Some(error_type) = error.error_type {
                parts.push(format!("type={error_type}"));
            }
            if let Some(message) = error.message {
                parts.push(format!("message={message}"));
            }
            (!parts.is_empty()).then(|| parts.join(" "))
        })
        .unwrap_or_else(|| "provider returned non-json error body".to_string());
    format!("xai TTS HTTP {status}: {safe_message}")
}

fn detect_mpeg(bytes: &[u8]) -> &'static str {
    if bytes.starts_with(b"ID3")
        || matches!(bytes.get(0..2), Some([0xff, second]) if second & 0xe0 == 0xe0)
    {
        "audio/mpeg"
    } else {
        "application/octet-stream"
    }
}
