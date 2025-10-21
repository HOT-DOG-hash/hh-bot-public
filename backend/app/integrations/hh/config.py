from __future__ import annotations

import os

from backend.app.core.config import settings
from backend.app.core.secrets import read_secret

API_BASE = settings.hh_api_base
AUTH_URL = settings.hh_auth_url
TOKEN_URL = settings.hh_token_url


def _env_or_secret(env_name: str, secret_name: str) -> str:
    value = os.getenv(env_name)
    if value:
        return value.strip()
    return read_secret(secret_name, env_fallback=env_name)


def get_client_id() -> str:
    return _env_or_secret("HH_CLIENT_ID", "hh_client_id")


def get_client_secret() -> str:
    return _env_or_secret("HH_CLIENT_SECRET", "hh_client_secret")


def get_redirect_uri(base_url: str | None = None) -> str:
    base = (base_url or settings.base_url_normalized).rstrip("/")
    return f"{base}/oauth/hh/callback"
