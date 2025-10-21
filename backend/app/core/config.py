# app/core/config.py
from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PLACEHOLDER_VALUES: ClassVar[set[str]] = {
        "",
        "CHANGE_ME",
        "admin@example",
        "changeMe123!",
    }
    KNOWN_LEAKED_VALUES: ClassVar[set[str]] = {
        "npg_t6xcJGfQkvP0",
        "npg_RgxzuIv6b9lS",
        "XOIj5k1Q0qZovJne0OyW9HvaEl6KFE8c8JkimOdavVYMDfz5rYA+Go1TRBhPXpwB",
        "Q!w2e3r4",
        "SRxrGqElL4RsNzBs9w3w83gtanvtA6swrCqevymeKhsBehARxXkGX/AenCvpzz9p",
        "7865199704:AAHjn5iTdVp7FM-VV2nMbzdhLWDyEq8fV8k",
        "eyJhIjoiYTY2ZDYzZTZkMjEwNzA5NjFhMmZkODI1ZGRiMGEwMDUiLCJ0IjoiOTc0NTNjNjAtNGZlNi00NzVhLThmOWMtYzQxZGUxZTdiZjVmIiwicyI6Ik56Z3pORFJqWmpFdE5qZGpNeTAwTkRJeUxXRTJNR010TmpkbE5HTXhNR0k1WVRsaiJ9",
    }

    # --- App ---
    app_name: str = Field("hh_backend", alias="APP_NAME")
    app_env: str = Field("development", alias="APP_ENV")
    app_debug: bool = Field(True, alias="APP_DEBUG")

    # --- Database ---
    database_url: str | None = Field(None, alias="DATABASE_URL")
    database_url_sqlite: str = Field("sqlite+aiosqlite:///./dev.db", alias="DATABASE_URL_SQLITE")

    # --- Redis ---
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # --- Security ---
    secret_key: str = Field("dev-secret-key", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # --- Admin ---
    admin_user: str = Field("dev-admin-user", alias="ADMIN_USER")
    admin_pass: str = Field("dev-admin-pass", alias="ADMIN_PASS")
    admin_secret_token: str = Field("dev-admin-token", alias="ADMIN_SECRET_TOKEN")
    admin_basic_realm: str = Field("HHOFFER Admin", alias="ADMIN_BASIC_REALM")

    # --- Logging ---
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_file: str = Field("logs/app.log", alias="LOG_FILE")

    # --- External APIs & integrations ---
    hh_api_base: str = Field("https://api.hh.ru", alias="HH_API_BASE")
    hh_auth_url: str = Field("https://hh.ru/oauth/authorize", alias="HH_AUTH_URL")
    hh_token_url: str = Field("https://hh.ru/oauth/token", alias="HH_TOKEN_URL")
    base_url: str = Field("http://localhost:8000", alias="BASE_URL")
    premium_enabled: bool = Field(False, alias="PREMIUM_ENABLED")
    payment_provider: str = Field("yoomoney", alias="PAYMENT_PROVIDER")
    yoomoney_api_base: str = Field("https://api.yookassa.ru/v3", alias="YOOMONEY_API_BASE")
    yoomoney_timeout: float = Field(12.0, alias="YOOMONEY_TIMEOUT")
    yoomoney_webhook_secret: str | None = Field(None, alias="YOOMONEY_WEBHOOK_SECRET")
    yoomoney_token: str | None = Field(None, alias="YOOMONEY_TOKEN")
    telegram_bot_token: str | None = Field(None, alias="TELEGRAM_BOT_TOKEN")
    cf_tunnel_token: str | None = Field(None, alias="CF_TUNNEL_TOKEN")

    # --- CORS ---
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost", "http://127.0.0.1"],
        alias="CORS_ORIGINS",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "case_sensitive": False,
    }

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value):
        if isinstance(value, str):
            candidate = value.strip()
            if candidate.startswith("[") and candidate.endswith("]"):
                try:
                    import json

                    parsed = json.loads(candidate)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:  # pragma: no cover - best effort parsing
                    pass
            return [item.strip() for item in candidate.split(",") if item.strip()]
        return value

    @property
    def effective_database_url(self) -> str:
        return self.database_url or self.database_url_sqlite

    @property
    def base_url_normalized(self) -> str:
        return self.base_url.rstrip("/")

    @staticmethod
    def _as_secret(value: Any) -> str | None:
        if value is None:
            return None
        return str(value).strip()

    def ensure_no_placeholders(self) -> None:
        for field_name in (
            "secret_key",
            "admin_secret_token",
            "admin_pass",
            "admin_user",
            "yoomoney_token",
            "telegram_bot_token",
            "cf_tunnel_token",
        ):
            raw = self._as_secret(getattr(self, field_name, None))
            if not raw:
                continue
            if raw in self.PLACEHOLDER_VALUES or raw in self.KNOWN_LEAKED_VALUES:
                raise ValueError(f"{field_name} uses placeholder or leaked value")


settings = Settings()
settings.ensure_no_placeholders()
