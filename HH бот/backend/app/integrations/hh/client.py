from __future__ import annotations

import hashlib
import json
from typing import Any

import httpx

from backend.app.core.logging import logger
from backend.app.core.redis import init_redis

from .config import API_BASE

_TIMEOUT = httpx.Timeout(12.0, connect=5.0)
_USER_AGENT = "HHOfferBot/1.0"


class HHAPIError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class HHUnauthorized(HHAPIError):
    """HeadHunter вернул 401."""


def _auth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": _USER_AGENT,
        "Accept": "application/json",
    }


async def get_me(access_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(
        base_url=API_BASE, timeout=_TIMEOUT, headers=_auth_headers(access_token)
    ) as client:
        try:
            response = await client.get("/me")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 401:
                logger.warning("hh_get_me_unauthorized", status=status)
                raise HHUnauthorized("HeadHunter profile unauthorized", status=status) from exc
            logger.warning("hh_get_me_failed", status=status)
            raise HHAPIError("HeadHunter profile request failed", status=status) from exc
        except httpx.HTTPError as exc:
            logger.warning("hh_get_me_transport_error")
            raise HHAPIError("HeadHunter profile request failed") from exc
    return response.json()


def _cache_key(params: dict[str, Any], namespace: str | None = None) -> str:
    payload = {"params": params, "namespace": namespace or ""}
    normalized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"hh:vacancies:{digest}"


async def search_vacancies(
    access_token: str,
    params: dict[str, Any],
    cache_ttl: int = 60,
    cache_namespace: str | None = None,
) -> dict[str, Any]:
    ttl = max(60, min(cache_ttl, 300))
    redis = None
    key = None

    try:
        redis = await init_redis()
    except Exception:  # pragma: no cover - Redis optional
        logger.warning("hh_cache_unavailable")

    if redis:
        key = _cache_key(params, namespace=cache_namespace)
        try:
            cached = await redis.get(key)
        except Exception:
            cached = None
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                logger.warning("hh_cache_decode_failed", key=key)

    async with httpx.AsyncClient(
        base_url=API_BASE, timeout=_TIMEOUT, headers=_auth_headers(access_token)
    ) as client:
        try:
            response = await client.get("/vacancies", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 401:
                logger.warning("hh_vacancies_unauthorized", status=status)
                raise HHUnauthorized("HeadHunter unauthorized", status=status) from exc
            logger.warning("hh_vacancies_failed", status=status)
            raise HHAPIError("HeadHunter vacancies request failed", status=status) from exc
        except httpx.HTTPError as exc:
            logger.warning("hh_vacancies_transport_error")
            raise HHAPIError("HeadHunter vacancies request failed") from exc
    data = response.json()

    if redis and key:
        try:
            await redis.set(key, json.dumps(data, ensure_ascii=False), ex=ttl)
        except Exception:
            logger.warning("hh_cache_store_failed", key=key, ttl=ttl)
    return data
