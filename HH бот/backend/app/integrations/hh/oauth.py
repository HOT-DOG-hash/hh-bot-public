from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx

from backend.app.core.logging import logger

from .config import AUTH_URL, TOKEN_URL, get_client_id, get_client_secret

_DEFAULT_TIMEOUT = httpx.Timeout(12.0, connect=5.0)


def build_auth_url(redirect_uri: str, state: str, scope: str = "read") -> str:
    params = {
        "client_id": get_client_id(),
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }
    if scope:
        params["scope"] = scope
    return f"{AUTH_URL}?{urlencode(params)}"


async def _post_token(payload: dict[str, Any]) -> dict[str, Any]:
    auth = (get_client_id(), get_client_secret())
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        try:
            response = await client.post(TOKEN_URL, data=payload, auth=auth)
            response.raise_for_status()
        except httpx.TimeoutException as exc:  # pragma: no cover - network guard
            logger.error("hh_oauth_timeout", error=str(exc), grant_type=payload.get("grant_type"))
            raise RuntimeError("HeadHunter OAuth timeout") from exc
        except httpx.HTTPError as exc:
            status = getattr(exc.response, "status_code", "unknown")
            logger.warning("hh_oauth_error", status=status, grant_type=payload.get("grant_type"))
            raise RuntimeError("HeadHunter OAuth error") from exc
    return response.json()


async def exchange_code_for_tokens(code: str, redirect_uri: str) -> dict[str, Any]:
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    return await _post_token(payload)


async def refresh_tokens(refresh_token: str) -> dict[str, Any]:
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    return await _post_token(payload)
