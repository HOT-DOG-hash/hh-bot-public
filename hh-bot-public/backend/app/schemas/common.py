from __future__ import annotations

from pydantic import BaseModel


class TelegramIdentity(BaseModel):
    telegram_id: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class TelegramIdentityRequest(TelegramIdentity):
    """
    Dedicated subclass for semantic clarity when embedding user context into requests.
    """

    pass
