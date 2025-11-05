from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Awaitable, Callable, Dict, Literal, Optional

from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy import func, select, text

from backend.app.core.config import settings
from backend.app.core.db import get_engine, get_session_factory
from backend.app.models.auto_campaigns import (
    Campaign,
    CampaignAuditLog,
    CampaignRun,
    CampaignStatus,
)
from backend.app.telemetry.metrics import get_scheduler_lag, set_component_ready_state

UTC = timezone.utc
ComponentState = Literal["pass", "fail"]


@dataclass
class ComponentCheckResult:
    status: ComponentState
    latency_ms: float
    updated_at: datetime
    detail: Optional[str] = None


def _now() -> datetime:
    return datetime.now(tz=UTC)


async def _check_db() -> tuple[ComponentState, Optional[str]]:
    engine = get_engine()
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    session_factory = get_session_factory()
    async with session_factory() as session:
        active_stmt = select(func.count(Campaign.id)).where(Campaign.status == CampaignStatus.ACTIVE)
        active_count = (await session.execute(active_stmt)).scalar_one()
        if active_count:
            latest_run_stmt = select(func.max(CampaignRun.run_started_at))
            latest_run = (await session.execute(latest_run_stmt)).scalar_one()
            if latest_run is None:
                return "fail", "no campaign runs recorded for active campaigns"
            lag = _now() - latest_run
            if lag > timedelta(minutes=5):
                return "fail", f"last campaign run {int(lag.total_seconds())}s ago"
    return "pass", None


async def _check_redis() -> tuple[ComponentState, Optional[str]]:
    redis_url = settings.redis_url or os.getenv("REDIS_URL")
    if not redis_url:
        return "pass", "redis-url-missing"

    client: Optional[Redis] = None
    try:
        client = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        pong = await client.ping()
        if not pong:
            return "fail", "redis ping failed"

        violations: list[str] = []
        count = 0
        async for key in client.scan_iter(match="idempotency:*", count=25):
            ttl = await client.ttl(key)
            if ttl == -2:
                violations.append(f"{key}:missing")
                break
            if ttl == -1 or ttl > 900:
                violations.append(f"{key}:{ttl}")
                break
            count += 1
            if count >= 50:
                break

        if violations:
            return "fail", f"idempotency ttl violation ({violations[0]})"
        return "pass", None
    except Exception as exc:  # pragma: no cover - defensive
        return "fail", str(exc)
    finally:
        if client is not None:
            try:
                await client.aclose()
            except Exception:  # pragma: no cover - best effort cleanup
                pass


def _check_scheduler() -> tuple[ComponentState, Optional[str]]:
    lag = get_scheduler_lag() or 0.0
    if lag > 120.0:
        return "fail", f"scheduler lag {lag:.1f}s"
    return "pass", None


def _check_feature_flag(app: FastAPI) -> tuple[ComponentState, Optional[str]]:
    env_value = os.getenv("ENABLE_AUTO_CAMPAIGNS", "").strip().lower()
    enabled_by_env = env_value in {"1", "true", "yes", "on"}
    enabled_state = bool(getattr(app.state, "campaigns_enabled", False))
    if enabled_by_env or enabled_state:
        return "pass", None
    return "fail", "ENABLE_AUTO_CAMPAIGNS is disabled"


async def _check_idempotency_store() -> tuple[ComponentState, Optional[str]]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        cleanup_stmt = select(func.max(CampaignAuditLog.created_at)).where(
            CampaignAuditLog.action == "idempotency.cleanup"
        )
        cleanup_ts = (await session.execute(cleanup_stmt)).scalar_one_or_none()

        if cleanup_ts is None:
            recent_conflict_stmt = (
                select(func.max(CampaignAuditLog.created_at))
                .where(CampaignAuditLog.idempotency_key.is_not(None))
                .execution_options(populate_existing=True)
            )
            cleanup_ts = (await session.execute(recent_conflict_stmt)).scalar_one_or_none()

        if cleanup_ts is None:
            return "pass", "no-idempotency-events"

        age = _now() - cleanup_ts
        if age > timedelta(hours=1):
            return "fail", f"idempotency checkpoints older than {int(age.total_seconds() // 60)}m"
    return "pass", None


async def _run_scheduler(_: FastAPI) -> tuple[ComponentState, Optional[str]]:
    return _check_scheduler()


async def _run_feature_flag(app: FastAPI) -> tuple[ComponentState, Optional[str]]:
    return _check_feature_flag(app)


_CHECK_SEQUENCE: Dict[str, Callable[[FastAPI], Awaitable[tuple[ComponentState, Optional[str]]]]] = {
    "db": lambda _: _check_db(),
    "redis": lambda _: _check_redis(),
    "scheduler": _run_scheduler,
    "feature_flag": _run_feature_flag,
    "idempotency_store": lambda _: _check_idempotency_store(),
}


async def run_component_checks(app: FastAPI) -> Dict[str, ComponentCheckResult]:
    results: Dict[str, ComponentCheckResult] = {}

    for component, runner in _CHECK_SEQUENCE.items():
        started = perf_counter()
        status: ComponentState = "fail"
        detail: Optional[str] = None

        try:
            status, detail = await runner(app)
        except Exception as exc:  # pragma: no cover - defensive
            detail = str(exc)
            status = "fail"

        latency_ms = (perf_counter() - started) * 1000.0
        checked_at = _now()
        set_component_ready_state(component, status == "pass")
        results[component] = ComponentCheckResult(
            status=status,
            latency_ms=latency_ms,
            updated_at=checked_at,
            detail=detail,
        )
    return results


def summarise_results(results: Dict[str, ComponentCheckResult]) -> tuple[str, int]:
    fail_count = sum(1 for result in results.values() if result.status == "fail")
    overall = "ok" if fail_count == 0 else "fail"
    return overall, fail_count


def serialize_checks(results: Dict[str, ComponentCheckResult]) -> Dict[str, Dict[str, object]]:
    payload: Dict[str, Dict[str, object]] = {}
    for component, result in results.items():
        entry: Dict[str, object] = {
            "status": result.status,
            "latency_ms": round(result.latency_ms, 2),
            "updated_at": result.updated_at.isoformat(),
        }
        if result.detail:
            entry["detail"] = result.detail
        payload[component] = entry
    return payload
