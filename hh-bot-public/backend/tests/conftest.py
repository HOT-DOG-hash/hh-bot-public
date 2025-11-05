from __future__ import annotations

import os
from pathlib import Path

import pytest_asyncio
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient

from backend.app.seeding import DEFAULT_PLANS

os.environ.setdefault("CAMPAIGNS_ENABLED", "1")
os.environ.setdefault("YOOMONEY_WEBHOOK_SECRET", "test-webhook-secret")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASS", "secret")

from backend.app.core import db as db_module
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.models import Base

# Ensure metadata captures all declarative models required for tests
import backend.app.models.auto_campaigns  # noqa: F401
import backend.app.models.blacklist  # noqa: F401
import backend.app.models.payments  # noqa: F401
import backend.app.models.plan  # noqa: F401
import backend.app.models.quota  # noqa: F401
import backend.app.models.subscription  # noqa: F401
from backend.app.models.plan import Plan


TEST_DB_PATH = Path("test_auto_campaigns.db")
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _configure_test_environment() -> None:
    """
    Configure an isolated SQLite database and required env safeguards
    before the FastAPI lifespan starts.
    """

    os.environ["YOOMONEY_WEBHOOK_SECRET"] = "test-webhook-secret"
    os.environ["ADMIN_USER"] = "admin"
    os.environ["ADMIN_PASS"] = "secret"
    settings.database_url = TEST_DB_URL
    settings.database_url_sqlite = TEST_DB_URL
    db_module._engine = None
    db_module._session_factory = None

    engine = db_module.get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    session_factory = db_module.get_session_factory()
    async with session_factory() as session:
        await session.execute(sa.text("PRAGMA foreign_keys=ON"))  # type: ignore[attr-defined]
        for plan in DEFAULT_PLANS:
            session.add(Plan(**plan))
        await session.commit()

    try:
        yield
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()
        db_module._engine = None
        db_module._session_factory = None
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()


# �ࠢ��쭠� �ᨭ�஭��� 䨪���� ������ ��� httpx 0.28+
@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
