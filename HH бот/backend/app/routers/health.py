from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.db import get_engine

router = APIRouter(tags=["health"], prefix="/api")


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    checks: dict[str, str]
    version: str | None = None


async def _check_db() -> str:
    try:
        engine = get_engine()
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:  # pragma: no cover - defensive reporting
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"db:{exc.__class__.__name__}"
        )


async def _check_redis() -> str:
    url = settings.redis_url or os.getenv("REDIS_URL", "").strip()
    if not url:
        return "skip"
    client: Redis | None = None
    try:
        client = Redis.from_url(url, encoding="utf-8", decode_responses=True)
        pong = await client.ping()
        if not pong:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="redis:ping_failed"
            )
        return "ok"
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive reporting
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"redis:{exc.__class__.__name__}",
        )
    finally:
        if client is not None:
            await client.aclose()


def _overall_status(checks: dict[str, str]) -> Literal["ok", "degraded"]:
    return "ok" if all(value in ("ok", "skip") for value in checks.values()) else "degraded"


@router.get("/health")
async def health(strict: bool = Query(False, description="HTTP 503 если есть 'fail'")):
    checks: dict[str, str] = {}
    status_code = status.HTTP_200_OK

    try:
        checks["db"] = await _check_db()
    except HTTPException as exc:
        status_code = max(status_code, exc.status_code)
        checks["db"] = str(exc.detail)

    try:
        checks["redis"] = await _check_redis()
    except HTTPException as exc:
        status_code = max(status_code, exc.status_code)
        checks["redis"] = str(exc.detail)

    overall = _overall_status(checks)
    payload = HealthResponse(status=overall, checks=checks, version=os.getenv("APP_VERSION"))

    if strict and overall != "ok":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    if overall != "ok":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(status_code=status_code, content=payload.model_dump())


@router.get("/healthz", response_class=Response)
async def healthz() -> Response:
    return Response(content="ok", media_type="text/plain", status_code=status.HTTP_200_OK)
