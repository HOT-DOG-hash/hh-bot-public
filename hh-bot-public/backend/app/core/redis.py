from redis.asyncio import Redis
from backend.app.core.config import settings

redis: Redis | None = None

async def init_redis() -> Redis:
    global redis
    if redis is None:
        redis = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return redis

async def close_redis():
    global redis
    if redis:
        await redis.aclose()
        redis = None

