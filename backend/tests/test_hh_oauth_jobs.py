from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from backend.app.core import redis as redis_module
from backend.app.integrations.hh import client as hh_client
from backend.app.models import Subscription, User
from backend.app.routers import jobs as jobs_router
from sqlalchemy import select


class _FakeRedis:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self.storage[key] = value

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.storage[key] = value

    async def get(self, key: str) -> str | None:
        return self.storage.get(key)

    async def delete(self, key: str) -> None:
        self.storage.pop(key, None)

    async def aclose(self) -> None:
        return None


@pytest.fixture
def fake_redis(monkeypatch):
    stub = _FakeRedis()

    async def _init() -> _FakeRedis:
        return stub

    monkeypatch.setattr(redis_module, "init_redis", _init)
    monkeypatch.setattr(redis_module, "redis", stub)
    return stub


@pytest.mark.asyncio
async def test_hh_login_redirects(client, session_factory, fake_redis, monkeypatch):
    monkeypatch.setenv("HH_CLIENT_ID", "test-client")
    monkeypatch.setenv("HH_CLIENT_SECRET", "test-secret")

    response = await client.get("/oauth/hh/login", params={"chat_id": "555"})
    assert response.status_code == 302

    location = response.headers.get("location")
    assert location

    parsed = urlparse(location)
    assert parsed.scheme in {"http", "https"}
    params = parse_qs(parsed.query)
    assert params.get("client_id") == ["test-client"]
    assert params.get("response_type") == ["code"]
    state = params.get("state", [None])[0]
    assert state

    redis_key = f"hh:oauth:state:{state}"
    stored_user_ref = fake_redis.storage.get(redis_key)
    assert stored_user_ref is not None

    async_sessionmaker = session_factory
    async with async_sessionmaker() as session:
        user = (await session.execute(select(User).where(User.tg_id == "555"))).scalar_one()
        assert stored_user_ref == str(user.id)


@pytest.mark.asyncio
async def test_jobs_search_requires_subscription(session_factory, client):
    now = datetime.now(timezone.utc)
    async_sessionmaker = session_factory
    async with async_sessionmaker() as session:
        user = User(
            tg_id="user-1",
            is_active=True,
            last_activity=now,
            hh_access_token="token-123",
            hh_token_expires_at=now + timedelta(hours=1),
        )
        session.add(user)
        await session.commit()

    response = await client.get(
        "/jobs/search", params={"q": "python"}, headers={"X-User-Id": "user-1"}
    )
    assert response.status_code == 402


@pytest.mark.asyncio
async def test_jobs_search_with_subscription(session_factory, client, monkeypatch):
    now = datetime.now(timezone.utc)
    async_sessionmaker = session_factory
    async with async_sessionmaker() as session:
        user = User(
            tg_id="user-2",
            is_active=True,
            last_activity=now,
            hh_access_token="token-live",
            hh_refresh_token="refresh-token",
            hh_token_expires_at=now + timedelta(hours=2),
        )
        session.add(user)
        await session.flush()
        subscription = Subscription(
            user_id=user.id,
            plan="premium-month",
            status="active",
            active=True,
            valid_until=now + timedelta(days=2),
            auto_renew=False,
        )
        session.add(subscription)
        await session.commit()

    calls: list[dict[str, object]] = []

    async def fake_search_vacancies(access_token: str, params: dict[str, object], **kwargs):
        calls.append({"token": access_token, "params": params})
        return {"items": [{"name": "Python Developer"}], "found": 1}

    monkeypatch.setattr(hh_client, "search_vacancies", fake_search_vacancies)
    monkeypatch.setattr(jobs_router, "search_vacancies", fake_search_vacancies)

    response = await client.get(
        "/jobs/search", params={"q": "python"}, headers={"X-User-Id": "user-2"}
    )
    assert response.status_code == 200
    assert response.json() == {"items": [{"name": "Python Developer"}], "found": 1}
    assert len(calls) == 1
    assert calls[0]["token"] == "token-live"
    assert calls[0]["params"]["text"] == "python"
