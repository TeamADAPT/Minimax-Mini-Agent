"""Crew nova configuration map."""

CREW = {
    "echo": {
        "model": "qwen/qwen3.5-397b-a17b",
        "provider": "nvidia",
        "window_name": "Echo CLI",
    },
    "skipper": {
        "model": "deepseek-v4-flash",
        "provider": "deepseek",
        "window_name": "Skipper CLI",
    },
    "iris": {
        "model": "qwen/qwen3.5-397b-a17b",
        "provider": "nvidia",
        "window_name": "Iris CLI",
    },
    "zap": {
        "model": "deepseek-v4-flash",
        "provider": "deepseek",
        "window_name": "Zap CLI",
    },
    "forge": {
        "model": "deepseek-v4-flash",
        "provider": "deepseek",
        "window_name": "Forge CLI",
    },
    "synergy": {
        "model": "deepseek-v4-flash",
        "provider": "deepseek",
        "window_name": "Synergy CLI",
    },
    "tecton": {
        "model": "qwen/qwen3.5-397b-a17b",
        "provider": "nvidia",
        "window_name": "Tecton CLI",
    },
}

CREW_ORDER = ("echo", "skipper", "iris", "zap", "forge", "synergy", "tecton")


def window_name(agent: str) -> str:
    """Return the expected visible terminal title for a crew nova."""
    return CREW[agent]["window_name"]


def profile_root(agent: str) -> str:
    """Return the Hermes profile root for a crew nova."""
    return f"/home/x/.hermes/profiles/{agent}"
