from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import settings
from backend.app.models import Base  # noqa: F401 - exported for Alembic

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    url = settings.database_url or settings.database_url_sqlite
    if not url:
        raise RuntimeError("DATABASE_URL is required for database access")
    return url


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_database_url(),
            echo=settings.app_debug,
            pool_pre_ping=True,
            future=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_db() -> AsyncSession:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session
