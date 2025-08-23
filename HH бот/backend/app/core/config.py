# app/core/config.py
from __future__ import annotations

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    # --- App ---
    app_name: str = Field("hh_backend", alias="APP_NAME")
    app_env: str = Field("development", alias="APP_ENV")
    app_debug: bool = Field(True, alias="APP_DEBUG")

    # --- Database ---
    # В prod используем DATABASE_URL (Postgres).
    # В dev можно не задавать DATABASE_URL — возьмём из DATABASE_URL_SQLITE.
    database_url: Optional[str] = Field(None, alias="DATABASE_URL")
    database_url_sqlite: str = Field("sqlite+aiosqlite:///./dev.db", alias="DATABASE_URL_SQLITE")

    # --- Redis ---
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # --- Security ---
    secret_key: str = Field(..., alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # --- Admin ---
    admin_secret_token: str = Field(..., alias="ADMIN_SECRET_TOKEN")

    # --- Logging ---
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_file: str = Field("logs/app.log", alias="LOG_FILE")

    # --- External APIs ---
    hh_api_base: str = Field("https://api.hh.ru", alias="HH_API_BASE")

    # --- CORS ---
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost", "http://127.0.0.1"],
        alias="CORS_ORIGINS",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",       # лишние ключи в .env игнорируем
        "case_sensitive": False, # допускаем разный регистр имён переменных
    }

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v):
        # Поддержка: "a,b" | "a, b" | '["a","b"]'
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @property
    def effective_database_url(self) -> str:
        """
        Prod: settings.database_url (Postgres).
        Dev:  fallback на SQLite, если DATABASE_URL не задан.
        """
        return self.database_url or self.database_url_sqlite


settings = Settings()
