# backend/app/routers/health.py
from __future__ import annotations

import os
from typing import Dict, Literal

from fastapi import APIRouter, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from redis.asyncio import from_url as redis_from_url

router = APIRouter(tags=["health"])

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    checks: Dict[str, str]

async def _check_redis() -> str:
    url = os.getenv("REDIS_URL", "").strip()
    if not url:
        return "skip"
    try:
        r = redis_from_url(url, encoding="utf-8", decode_responses=True)
        pong = await r.ping()
        await r.close()
        return "ok" if pong else "fail"
    except Exception as e:
        return f"fail:{e.__class__.__name__}"

async def _check_db() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return "skip"
    engine = create_async_engine(url, future=True)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception as e:
        return f"fail:{e.__class__.__name__}"
    finally:
        await engine.dispose()

def _overall_status(checks: Dict[str, str]) -> Literal["ok", "degraded"]:
    return "ok" if all(v in ("ok", "skip") for v in checks.values()) else "degraded"

@router.get("/health", response_model=HealthResponse)
async def health(strict: bool = Query(False, description="Вернуть 503, если есть 'fail'")):
    checks: Dict[str, str] = {
        "redis": await _check_redis(),
        "db": await _check_db(),
    }
    overall = _overall_status(checks)
    if strict and overall != "ok":
        return Response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=HealthResponse(status=overall, checks=checks).model_dump_json(),
            media_type="application/json",
        )
    return HealthResponse(status=overall, checks=checks)

@router.get("/healthz", response_class=Response)
async def healthz(strict: bool = Query(False, description="Вернуть 503, если есть 'fail'")):
    """
    Узкий текстовый зонд, совместимый с некоторыми оркестраторами.
    Nginx свой /healthz держит локально; этот эндпойнт — backend-эквивалент.
    """
    checks: Dict[str, str] = {
        "redis": await _check_redis(),
        "db": await _check_db(),
    }
    overall = _overall_status(checks)
    code = status.HTTP_200_OK if (overall == "ok" or not strict) else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(content=("ok" if overall == "ok" else "degraded"), media_type="text/plain", status_code=code)
