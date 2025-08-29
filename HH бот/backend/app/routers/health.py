from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from redis.asyncio import from_url as redis_from_url

from backend.app.core.config import settings

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    checks: dict

@router.get("/health", response_model=HealthResponse)
async def health():
    checks: dict[str, str] = {}

    # --- Redis check ---
    try:
        r = redis_from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        pong = await r.ping()
        await r.close()
        checks["redis"] = "ok" if pong else "fail"
    except Exception as e:
        checks["redis"] = f"fail: {e.__class__.__name__}"

    # --- DB check ---
    try:
        engine = create_async_engine(settings.database_url, future=True)
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"fail: {e.__class__.__name__}"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return HealthResponse(status=overall, checks=checks)

