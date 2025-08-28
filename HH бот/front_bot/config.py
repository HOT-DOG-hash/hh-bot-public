# HH бот/front_bot/config.py
from __future__ import annotations
import os
import logging

def _sanitize(s: str | None) -> str | None:
    if not s:
        return None
    s = s.strip().strip('"').strip("'").strip()
    if s.startswith("<") and s.endswith(">"):
        s = s[1:-1].strip()
    return s or None

def read_token_from_env() -> str | None:
    """
    МЯГКАЯ версия: ничего не падает.
    Возвращает токен из окружения либо None. Логи — warning, без sys.exit.
    """
    for key in ("TELEGRAM_BOT_TOKEN", "BOT_TOKEN"):
        val = _sanitize(os.getenv(key))
        if val and ":" in val and len(val) >= 30:
            return val
    logging.warning("config.read_token_from_env: токен в окружении не найден или в неверном формате.")
    return None
