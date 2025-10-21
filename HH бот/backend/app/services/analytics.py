from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Mapping
from typing import Any

from backend.app.core.logging import logger

PII_KEYS = {"user_id", "user", "user_token", "vacancy_id", "email", "tg_id"}


def _mask_identifier(value: object) -> str:
    raw = str(value)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return digest[:12]


def _sanitize(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}

    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, Mapping):
            sanitized[key] = _sanitize(value)
            continue
        if key in PII_KEYS or key.endswith("_id"):
            sanitized[key] = _mask_identifier(value)
        else:
            sanitized[key] = value
    return sanitized


async def _emit_async(event: str, payload: Mapping[str, Any]) -> None:
    try:
        logger.info("analytics_event", event=event, payload=dict(payload))
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("analytics_emit_failed", event=event)


def track_event(event: str, payload: Mapping[str, Any] | None = None) -> None:
    data = _sanitize(payload)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # pragma: no cover - sync fallback
        logger.info("analytics_event", event=event, payload=data)
        return
    loop.create_task(_emit_async(event, data))
