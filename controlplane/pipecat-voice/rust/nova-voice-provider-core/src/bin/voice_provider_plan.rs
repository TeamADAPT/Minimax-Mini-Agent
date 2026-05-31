//! Command-line voice provider route planner.

use std::env;
use std::str::FromStr;

use clap::Parser;
use nova_voice_provider_core::{
    default_provider_config, plan_from_config, ProviderKind, VoiceCapability, VoiceRouteRequest,
};

/// Plan a safe voice provider route without printing secret values.
#[derive(Debug, Parser)]
#[command(name = "voice-provider-plan")]
#[command(about = "Plan a Nova voice provider route without exposing credentials")]
struct Args {
    /// Provider id: deepgram or xai.
    #[arg(long, default_value = "deepgram")]
    provider: String,

    /// Logical route id such as iris.direct or room.main.
    #[arg(long, default_value = "voice.default")]
    route_id: String,

    /// Required capability. Can be passed multiple times.
    #[arg(long = "capability", default_values_t = [String::from("realtime")])]
    capabilities: Vec<String>,

    /// Allow experimental providers such as xai.
    #[arg(long, default_value_t = false)]
    allow_experimental: bool,

    /// Browser will connect directly to the provider using an ephemeral credential.
    #[arg(long, default_value_t = false)]
    browser_direct: bool,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    let provider_kind = ProviderKind::from_str(&args.provider)?;
    let config = default_provider_config(provider_kind);
    let required_capabilities = args
        .capabilities
        .iter()
        .map(|capability| VoiceCapability::from_str(capability))
        .collect::<Result<Vec<_>, _>>()?;
    let available_env = config
        .required_env
        .iter()
        .filter(|name| env::var_os(name).is_some())
        .cloned()
        .collect::<Vec<_>>();
    let request = VoiceRouteRequest {
        route_id: args.route_id,
        required_capabilities,
        allow_experimental: args.allow_experimental,
        browser_direct: args.browser_direct,
        available_env,
    };
    let plan = plan_from_config(&config, &request)?;
    println!("{}", serde_json::to_string_pretty(&plan)?);
    Ok(())
}
