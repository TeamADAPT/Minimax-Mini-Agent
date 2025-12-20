"""
Secrets Loader for NovaInfra
Loads credentials from /adapt/secrets/ directory
"""

import os
from pathlib import Path
from typing import Dict, Optional


class NovaSecrets:
    """Loads and manages secrets for NovaInfra services"""

    def __init__(self, secrets_path: str = "/adapt/secrets"):
        """
        Initialize secrets loader

        Args:
            secrets_path: Path to secrets directory
        """
        self.secrets_path = Path(secrets_path)
        self.secrets = {}
        self._load_all_secrets()

    def _load_all_secrets(self):
        """Load all secrets from files in secrets directory"""
        if not self.secrets_path.exists():
            print(f"⚠️  Secrets directory not found: {self.secrets_path}")
            return

        for secrets_file in self.secrets_path.glob("*.env"):
            self._load_secrets_file(secrets_file)

    def _load_secrets_file(self, file_path: Path):
        """Load secrets from a single file"""
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")

                        # Expand variables in value
                        value = os.path.expandvars(value)

                        self.secrets[key] = value

        except Exception as e:
            print(f"⚠️  Error loading secrets from {file_path}: {e}")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value

        Args:
            key: Secret key
            default: Default value if key not found

        Returns:
            str: Secret value or default
        """
        return self.secrets.get(key, default)

    def get_nats_config(self) -> Dict[str, str]:
        """Get NATS configuration"""
        user = self.get("NATS_USER", "nats")
        password = self.get("NATS_PASSWORD", "password")
        host = self.get("NATS_HOST", "localhost")
        port = self.get("NATS_PORT", "18020")

        # Build URL manually (don't use NATS_URL as it may have unexpanded variables)
        url = f"nats://{user}:{password}@{host}:{port}"

        return {
            "user": user,
            "password": password,
            "url": url,
            "host": host,
            "port": port
        }

    def get_postgres_config(self) -> Dict[str, str]:
        """Get PostgreSQL configuration"""
        return {
            "host": self.get("POSTGRES_HOST", "localhost"),
            "port": self.get("POSTGRES_PORT", "5432"),
            "user": self.get("POSTGRES_USER", "postgres"),
            "password": self.get("POSTGRES_PASSWORD", "password"),
            "database": self.get("POSTGRES_DB", "postgres")
        }


# Global secrets instance
_default_secrets: Optional[NovaSecrets] = None


def get_secrets() -> NovaSecrets:
    """Get the global secrets instance"""
    global _default_secrets
    if _default_secrets is None:
        _default_secrets = NovaSecrets()
    return _default_secrets


# Quick test
if __name__ == "__main__":
    secrets = get_secrets()
    nats_config = secrets.get_nats_config()

    print("NATS Configuration:")
    print(f"  User: {nats_config['user']}")
    print(f"  Password: {'*' * len(nats_config['password'])}")
    print(f"  URL: {nats_config['url']}")
    print(f"  Total secrets loaded: {len(secrets.secrets)}")

    print("\nSample secrets:")
    for key in list(secrets.secrets.keys())[:5]:
        value = secrets.secrets[key]
        # Mask passwords and sensitive values
        if 'PASSWORD' in key or 'SECRET' in key or 'KEY' in key:
            value = '*' * len(value)
        print(f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}")
