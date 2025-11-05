from __future__ import annotations

import subprocess
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request, Response, status as http_status

from backend.app.services.health_checks import run_component_checks, serialize_checks, summarise_results

router = APIRouter(tags=["health"])


def _get_git_ref() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
            .decode("utf-8")
            .strip()
        )
    except Exception:  # pragma: no cover - fallback if git недоступен
        return "unknown"


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request, response: Response) -> dict[str, Any]:
    checks = await run_component_checks(request.app)
    overall, fail_count = summarise_results(checks)
    if overall != "ok":
        response.status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": overall,
        "checks": serialize_checks(checks),
        "version": os.getenv("APP_VERSION"),
        "git_ref": _get_git_ref(),
        "build_time": datetime.now(timezone.utc).isoformat(),
    }
