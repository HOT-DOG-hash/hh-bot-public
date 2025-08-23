from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.models import Base

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_pre_ping=settings.app_env == "production",  # только в проде
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
