//! ADR-002 envelope parsing and construction for wasm64 tool communication over
//! NATS.
use serde::{Deserialize, Serialize};
use std::fmt;

// ---------------------------------------------------------------------------
// Envelope types (ADR-002 L006)
// ---------------------------------------------------------------------------

/// Criticality level per Z-Pure (ADR-002 L009)
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DiagnosticLevel {
    CoreSafety,
    RuntimeCapacity,
    UxTuning,
    Experimental,
}

impl fmt::Display for DiagnosticLevel {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DiagnosticLevel::CoreSafety => write!(f, "core_safety"),
            DiagnosticLevel::RuntimeCapacity => write!(f, "runtime_capacity"),
            DiagnosticLevel::UxTuning => write!(f, "ux_tuning"),
            DiagnosticLevel::Experimental => write!(f, "experimental"),
        }
    }
}

/// A single diagnostic entry in the envelope
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Diagnostic {
    pub level: DiagnosticLevel,
    pub message: String,
}

/// ADR-002 envelope for wasm64 tool communication
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Envelope {
    pub envelope_version: u8,
    pub request_id: String,
    pub payload: serde_json::Value,
    #[serde(default)]
    pub diagnostics: Vec<Diagnostic>,
}

impl Envelope {
    /// Create a success response envelope
    pub fn success(request_id: String, content: String) -> Self {
        let size = content.len();
        Envelope {
            envelope_version: 1,
            request_id,
            payload: serde_json::json!({"content": content, "size": size}),
            diagnostics: vec![],
        }
    }

    /// Create an error response envelope with diagnostics
    pub fn error(request_id: String, level: DiagnosticLevel, message: String) -> Self {
        Envelope {
            envelope_version: 1,
            request_id,
            payload: serde_json::json!({"content": "", "size": 0}),
            diagnostics: vec![Diagnostic { level, message }],
        }
    }

    /// Parse a JSON string into an envelope
    pub fn from_json(json: &str) -> Result<Self, String> {
        let env: Envelope =
            serde_json::from_str(json).map_err(|e| format!("Invalid envelope JSON: {}", e))?;

        // ADR-002 L006: validate envelope_version
        if env.envelope_version != 1 {
            return Err(format!(
                "Unsupported envelope version: {}",
                env.envelope_version
            ));
        }

        // Validate request_id is present
        if env.request_id.is_empty() {
            return Err("Missing request_id in envelope".to_string());
        }

        Ok(env)
    }

    /// Serialize envelope to JSON
    pub fn to_json(&self) -> String {
        serde_json::to_string_pretty(self).unwrap_or_else(|_| {
            String::from(r#"{"envelope_version":1,"request_id":"err-serialize","payload":{"content":"","size":0},"diagnostics":[{"level":"runtime_capacity","message":"Failed to serialize response"}]}"#)
        })
    }
}

// ---------------------------------------------------------------------------
// Convenience: generate a traceable request_id
// ---------------------------------------------------------------------------

/// Generate a traceable request_id from PID + timestamp
pub fn make_request_id() -> String {
    let pid = std::process::id();
    let ts = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    format!("agent-{}-{:x}", pid, ts)
}
