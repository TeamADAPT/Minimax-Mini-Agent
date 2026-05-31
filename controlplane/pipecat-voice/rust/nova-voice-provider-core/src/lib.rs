//! Rust-owned voice provider contract for Nova CommsOps.
//!
//! The live gateway can keep Deepgram as the default while this crate owns the
//! provider vocabulary, credential policy, endpoint defaults, and experimental
//! xAI gating.

use serde::{Deserialize, Serialize};
use thiserror::Error;
use url::Url;

/// Deepgram Agent API websocket used by the current CX Pipe gateway.
pub const DEEPGRAM_REALTIME_URL: &str = "wss://agent.deepgram.com/v1/agent/converse";

/// Deepgram short-lived auth grant endpoint.
pub const DEEPGRAM_TOKEN_GRANT_URL: &str = "https://api.deepgram.com/v1/auth/grant";

/// xAI realtime voice websocket endpoint.
pub const XAI_REALTIME_URL: &str = "wss://api.x.ai/v1/realtime";

/// xAI ephemeral client-secret endpoint for browser realtime sessions.
pub const XAI_CLIENT_SECRET_URL: &str = "https://api.x.ai/v1/realtime/client_secrets";

/// xAI text-to-speech endpoint.
pub const XAI_TTS_URL: &str = "https://api.x.ai/v1/tts";

/// xAI speech-to-text endpoint.
pub const XAI_STT_URL: &str = "https://api.x.ai/v1/stt";

/// Supported voice provider ids.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProviderKind {
    /// Deepgram Agent API, STT, and TTS surfaces.
    Deepgram,
    /// xAI/Grok voice APIs.
    Xai,
}

impl ProviderKind {
    /// Stable lowercase provider id.
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Deepgram => "deepgram",
            Self::Xai => "xai",
        }
    }
}

/// Voice capabilities a provider can expose.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum VoiceCapability {
    /// Speech-to-text.
    Stt,
    /// Text-to-speech.
    Tts,
    /// Bidirectional realtime speech session.
    Realtime,
}

/// Browser credential exposure policy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum BrowserCredentialPolicy {
    /// Browser must connect through a server-side proxy; no credential leaves the server.
    ServerProxyOnly,
    /// Browser may receive a short-lived token from this endpoint.
    EphemeralClientSecret {
        /// Server-side endpoint used to mint the ephemeral credential.
        mint_url: String,
        /// Header/subprotocol prefix the browser uses with the ephemeral token.
        client_prefix: String,
    },
}

/// Endpoint set for one provider.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProviderEndpoints {
    /// Realtime websocket URL.
    pub realtime: Option<String>,
    /// HTTP or websocket TTS URL.
    pub tts: Option<String>,
    /// HTTP or websocket STT URL.
    pub stt: Option<String>,
    /// Ephemeral browser credential mint URL.
    pub client_secret: Option<String>,
}

impl ProviderEndpoints {
    /// Validate every configured endpoint URL.
    ///
    /// Returns an error naming the bad field when any URL cannot be parsed.
    pub fn validate(&self) -> Result<(), VoiceProviderError> {
        for (field, value) in [
            ("realtime", &self.realtime),
            ("tts", &self.tts),
            ("stt", &self.stt),
            ("client_secret", &self.client_secret),
        ] {
            if let Some(url) = value {
                Url::parse(url).map_err(|_| VoiceProviderError::InvalidEndpoint {
                    provider: "unknown".to_string(),
                    field: field.to_string(),
                    value: url.clone(),
                })?;
            }
        }
        Ok(())
    }
}

/// Provider configuration without secret values.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProviderConfig {
    /// Provider id.
    pub kind: ProviderKind,
    /// Whether the provider can be selected.
    pub enabled: bool,
    /// Whether provider use requires explicit experimental opt-in.
    pub experimental: bool,
    /// Environment variable names required at runtime.
    pub required_env: Vec<String>,
    /// Supported capabilities.
    pub capabilities: Vec<VoiceCapability>,
    /// Endpoints used by the provider.
    pub endpoints: ProviderEndpoints,
    /// Browser credential policy.
    pub browser_policy: BrowserCredentialPolicy,
    /// Default realtime model when applicable.
    pub default_realtime_model: Option<String>,
}

impl ProviderConfig {
    /// Validate static config shape.
    pub fn validate(&self) -> Result<(), VoiceProviderError> {
        self.endpoints.validate()
    }

    /// Return true when the config advertises every requested capability.
    #[must_use]
    pub fn supports_all(&self, requested: &[VoiceCapability]) -> bool {
        requested
            .iter()
            .all(|capability| self.capabilities.contains(capability))
    }
}

/// Route-planning request.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VoiceRouteRequest {
    /// Logical route id, for example `iris.direct` or `room.main`.
    pub route_id: String,
    /// Required provider capabilities.
    pub required_capabilities: Vec<VoiceCapability>,
    /// Whether experimental providers may be selected.
    pub allow_experimental: bool,
    /// Whether the browser will connect directly to the provider.
    pub browser_direct: bool,
    /// Environment variables available to the provider process. Values are never stored.
    pub available_env: Vec<String>,
}

/// Provider route plan safe to expose to non-secret config surfaces.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VoiceRoutePlan {
    /// Provider selected for the route.
    pub provider: ProviderKind,
    /// Route id from the request.
    pub route_id: String,
    /// Capabilities satisfied by the provider.
    pub capabilities: Vec<VoiceCapability>,
    /// Provider endpoints.
    pub endpoints: ProviderEndpoints,
    /// Browser credential policy.
    pub browser_policy: BrowserCredentialPolicy,
    /// Default realtime model when applicable.
    pub default_realtime_model: Option<String>,
}

/// Voice provider planning failures.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum VoiceProviderError {
    /// Provider is disabled in config.
    #[error("provider {provider} is disabled")]
    Disabled {
        /// Provider id.
        provider: String,
    },
    /// Provider is experimental and the route did not opt in.
    #[error("provider {provider} requires experimental opt-in")]
    ExperimentalBlocked {
        /// Provider id.
        provider: String,
    },
    /// Required environment variable is missing.
    #[error("provider {provider} missing required environment variable {env}")]
    MissingEnv {
        /// Provider id.
        provider: String,
        /// Missing environment variable name.
        env: String,
    },
    /// Provider cannot satisfy a requested capability.
    #[error("provider {provider} missing requested capability {capability:?}")]
    MissingCapability {
        /// Provider id.
        provider: String,
        /// Missing capability.
        capability: VoiceCapability,
    },
    /// Endpoint URL failed validation.
    #[error("provider {provider} has invalid {field} endpoint {value}")]
    InvalidEndpoint {
        /// Provider id.
        provider: String,
        /// Endpoint field name.
        field: String,
        /// Invalid value.
        value: String,
    },
    /// Direct browser access would expose a long-lived server credential.
    #[error("provider {provider} cannot be used directly from browser without ephemeral secret")]
    BrowserCredentialBlocked {
        /// Provider id.
        provider: String,
    },
}

/// Common provider planning behavior.
pub trait VoiceProvider: Send + Sync {
    /// Return provider config.
    fn config(&self) -> &ProviderConfig;

    /// Return provider kind.
    fn kind(&self) -> ProviderKind {
        self.config().kind
    }

    /// Plan a safe provider route.
    fn plan(&self, request: &VoiceRouteRequest) -> Result<VoiceRoutePlan, VoiceProviderError> {
        plan_from_config(self.config(), request)
    }
}

/// Deepgram provider wrapper.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeepgramProvider {
    config: ProviderConfig,
}

impl DeepgramProvider {
    /// Create a Deepgram provider from config.
    #[must_use]
    pub const fn new(config: ProviderConfig) -> Self {
        Self { config }
    }

    /// Create the default Deepgram provider config used by CX Pipe.
    #[must_use]
    pub fn default_provider() -> Self {
        Self::new(default_deepgram_config())
    }
}

impl VoiceProvider for DeepgramProvider {
    fn config(&self) -> &ProviderConfig {
        &self.config
    }
}

/// xAI voice provider wrapper.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct XaiVoiceProvider {
    config: ProviderConfig,
}

impl XaiVoiceProvider {
    /// Create an xAI provider from config.
    #[must_use]
    pub const fn new(config: ProviderConfig) -> Self {
        Self { config }
    }

    /// Create the default guarded xAI provider config.
    #[must_use]
    pub fn default_provider() -> Self {
        Self::new(default_xai_config())
    }
}

impl VoiceProvider for XaiVoiceProvider {
    fn config(&self) -> &ProviderConfig {
        &self.config
    }
}

/// Return the default Deepgram config without secret values.
#[must_use]
pub fn default_deepgram_config() -> ProviderConfig {
    ProviderConfig {
        kind: ProviderKind::Deepgram,
        enabled: true,
        experimental: false,
        required_env: vec!["DEEPGRAM_API_KEY".to_string()],
        capabilities: vec![
            VoiceCapability::Stt,
            VoiceCapability::Tts,
            VoiceCapability::Realtime,
        ],
        endpoints: ProviderEndpoints {
            realtime: Some(DEEPGRAM_REALTIME_URL.to_string()),
            tts: None,
            stt: None,
            client_secret: Some(DEEPGRAM_TOKEN_GRANT_URL.to_string()),
        },
        browser_policy: BrowserCredentialPolicy::EphemeralClientSecret {
            mint_url: DEEPGRAM_TOKEN_GRANT_URL.to_string(),
            client_prefix: "Token ".to_string(),
        },
        default_realtime_model: None,
    }
}

/// Return the default guarded xAI voice config without secret values.
#[must_use]
pub fn default_xai_config() -> ProviderConfig {
    ProviderConfig {
        kind: ProviderKind::Xai,
        enabled: true,
        experimental: true,
        required_env: vec!["XAI_API_KEY".to_string()],
        capabilities: vec![
            VoiceCapability::Stt,
            VoiceCapability::Tts,
            VoiceCapability::Realtime,
        ],
        endpoints: ProviderEndpoints {
            realtime: Some(XAI_REALTIME_URL.to_string()),
            tts: Some(XAI_TTS_URL.to_string()),
            stt: Some(XAI_STT_URL.to_string()),
            client_secret: Some(XAI_CLIENT_SECRET_URL.to_string()),
        },
        browser_policy: BrowserCredentialPolicy::EphemeralClientSecret {
            mint_url: XAI_CLIENT_SECRET_URL.to_string(),
            client_prefix: "xai-client-secret.".to_string(),
        },
        default_realtime_model: Some("grok-voice-latest".to_string()),
    }
}

/// Build a safe route plan from provider config.
pub fn plan_from_config(
    config: &ProviderConfig,
    request: &VoiceRouteRequest,
) -> Result<VoiceRoutePlan, VoiceProviderError> {
    let provider = config.kind.as_str().to_string();
    if !config.enabled {
        return Err(VoiceProviderError::Disabled { provider });
    }
    if config.experimental && !request.allow_experimental {
        return Err(VoiceProviderError::ExperimentalBlocked { provider });
    }
    for env in &config.required_env {
        if !request
            .available_env
            .iter()
            .any(|available| available == env)
        {
            return Err(VoiceProviderError::MissingEnv {
                provider,
                env: env.clone(),
            });
        }
    }
    for capability in &request.required_capabilities {
        if !config.capabilities.contains(capability) {
            return Err(VoiceProviderError::MissingCapability {
                provider,
                capability: *capability,
            });
        }
    }
    config.validate().map_err(|error| match error {
        VoiceProviderError::InvalidEndpoint { field, value, .. } => {
            VoiceProviderError::InvalidEndpoint {
                provider: provider.clone(),
                field,
                value,
            }
        }
        other => other,
    })?;
    if request.browser_direct
        && matches!(
            config.browser_policy,
            BrowserCredentialPolicy::ServerProxyOnly
        )
    {
        return Err(VoiceProviderError::BrowserCredentialBlocked { provider });
    }
    Ok(VoiceRoutePlan {
        provider: config.kind,
        route_id: request.route_id.clone(),
        capabilities: request.required_capabilities.clone(),
        endpoints: config.endpoints.clone(),
        browser_policy: config.browser_policy.clone(),
        default_realtime_model: config.default_realtime_model.clone(),
    })
}

#[cfg(test)]
mod tests {
    use super::{
        default_deepgram_config, default_xai_config, BrowserCredentialPolicy, DeepgramProvider,
        ProviderKind, VoiceCapability, VoiceProvider, VoiceProviderError, VoiceRouteRequest,
        XaiVoiceProvider, XAI_CLIENT_SECRET_URL, XAI_REALTIME_URL,
    };

    fn realtime_request(provider_env: &str) -> VoiceRouteRequest {
        VoiceRouteRequest {
            route_id: "iris.direct".to_string(),
            required_capabilities: vec![VoiceCapability::Realtime],
            allow_experimental: false,
            browser_direct: true,
            available_env: vec![provider_env.to_string()],
        }
    }

    #[test]
    fn deepgram_default_plans_browser_realtime_with_ephemeral_policy() {
        let provider = DeepgramProvider::default_provider();
        let plan = provider
            .plan(&realtime_request("DEEPGRAM_API_KEY"))
            .expect("deepgram route should plan");

        assert_eq!(plan.provider, ProviderKind::Deepgram);
        assert_eq!(plan.capabilities, vec![VoiceCapability::Realtime]);
        assert!(matches!(
            plan.browser_policy,
            BrowserCredentialPolicy::EphemeralClientSecret { .. }
        ));
    }

    #[test]
    fn xai_default_requires_explicit_experimental_opt_in() {
        let provider = XaiVoiceProvider::default_provider();
        let error = provider
            .plan(&realtime_request("XAI_API_KEY"))
            .expect_err("xai must be guarded");

        assert_eq!(
            error,
            VoiceProviderError::ExperimentalBlocked {
                provider: "xai".to_string()
            }
        );
    }

    #[test]
    fn xai_default_plans_when_experimental_is_allowed() {
        let provider = XaiVoiceProvider::default_provider();
        let mut request = realtime_request("XAI_API_KEY");
        request.allow_experimental = true;

        let plan = provider.plan(&request).expect("xai route should plan");

        assert_eq!(plan.provider, ProviderKind::Xai);
        assert_eq!(plan.endpoints.realtime.as_deref(), Some(XAI_REALTIME_URL));
        assert_eq!(
            plan.endpoints.client_secret.as_deref(),
            Some(XAI_CLIENT_SECRET_URL)
        );
        assert_eq!(
            plan.default_realtime_model.as_deref(),
            Some("grok-voice-latest")
        );
    }

    #[test]
    fn missing_provider_env_is_rejected_without_exposing_values() {
        let provider = DeepgramProvider::default_provider();
        let error = provider
            .plan(&VoiceRouteRequest {
                route_id: "iris.direct".to_string(),
                required_capabilities: vec![VoiceCapability::Realtime],
                allow_experimental: false,
                browser_direct: true,
                available_env: Vec::new(),
            })
            .expect_err("missing env should fail");

        assert_eq!(
            error,
            VoiceProviderError::MissingEnv {
                provider: "deepgram".to_string(),
                env: "DEEPGRAM_API_KEY".to_string()
            }
        );
    }

    #[test]
    fn invalid_endpoint_is_rejected() {
        let mut config = default_deepgram_config();
        config.endpoints.realtime = Some("not a url".to_string());
        let provider = DeepgramProvider::new(config);

        let error = provider
            .plan(&realtime_request("DEEPGRAM_API_KEY"))
            .expect_err("invalid endpoint should fail");

        assert!(matches!(
            error,
            VoiceProviderError::InvalidEndpoint { field, .. } if field == "realtime"
        ));
    }

    #[test]
    fn xai_config_contains_all_voice_capabilities() {
        let config = default_xai_config();

        assert!(config.supports_all(&[
            VoiceCapability::Stt,
            VoiceCapability::Tts,
            VoiceCapability::Realtime,
        ]));
    }
}
