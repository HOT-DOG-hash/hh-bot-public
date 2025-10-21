from __future__ import annotations

import os
from pathlib import Path

SECRETS_DIR = Path("/run/secrets")


class SecretNotFoundError(RuntimeError):
    """Raised when a required secret cannot be resolved."""


def read_secret(name: str, env_fallback: str | None = None) -> str:
    """Return secret value from /run/secrets/{name} or environment fallback."""

    secret_path = SECRETS_DIR / name
    if secret_path.is_file():
        value = secret_path.read_text(encoding="utf-8").strip()
    elif env_fallback:
        value = os.getenv(env_fallback, "").strip()
    else:
        raise SecretNotFoundError(
            f"Secret '{name}' not found in /run/secrets and no fallback provided"
        )

    if not value:
        source = f"/run/secrets/{name}" if secret_path.is_file() else f"env:{env_fallback}"
        raise SecretNotFoundError(f"Secret '{name}' resolved from {source} is empty")

    return value


__all__ = ["read_secret", "SecretNotFoundError"]
