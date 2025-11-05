import json
import os

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...security import admin_guard

router = APIRouter(prefix="/api/admin", tags=["admin"])

class BroadcastIn(BaseModel):
    text: str
    chat_ids: list[int] | None = None  # если пусто — отправим всем

@router.post("/broadcasts")
async def broadcasts(payload: BroadcastIn, _: bool = Depends(admin_guard)):
    r = aioredis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    await r.lpush("broadcast_queue", json.dumps(payload.model_dump()))
    await r.close()
    return {"ok": True}
