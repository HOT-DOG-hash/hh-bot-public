from __future__ import annotations

import os
from typing import Iterable

from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.db import get_engine
from backend.app.core.redis import close_redis, init_redis

REQUIRED_ENV: tuple[str, ...] = (
    "BASE_URL",
    "DATABASE_URL",
    "SECRET_KEY",
    "ADMIN_SECRET_TOKEN",
    "ADMIN_USER",
    "ADMIN_PASS",
    "TELEGRAM_BOT_TOKEN",
    "YOOMONEY_WEBHOOK_SECRET",
)

PLACEHOLDER_VALUES = {"xxx", "changeme", "placeholder", "dev", "development"}


def _detect_missing(keys: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for key in keys:
        val = os.getenv(key, "").strip()
        if not val or val.lower() in PLACEHOLDER_VALUES:
            missing.append(key)
    return missing


def ensure_no_placeholders() -> None:
    """Fail fast if критический ENV отсутствует или задан плейсхолдером."""
    missing = _detect_missing(REQUIRED_ENV)
    if missing:
        raise RuntimeError(f"Missing or placeholder ENV: {', '.join(sorted(missing))}")


async def check_db() -> None:
    """Проверяет подключение к БД (SQLite/PG)."""
    engine = get_engine()
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def check_redis() -> str:
    """Проверяет доступность Redis. Возвращает 'ready' или 'skipped'."""
    redis_url = os.getenv("REDIS_URL") or settings.redis_url
    if not redis_url:
        return "skipped"
    client = await init_redis()
    try:
        await client.ping()
    finally:
        await close_redis()
    return "ready"
