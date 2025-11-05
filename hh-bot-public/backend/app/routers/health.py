from __future__ import annotations

import os
import os
from typing import Dict

from fastapi import APIRouter, Query, Request, Response, status
from fastapi.responses import JSONResponse

from backend.app.services.health_checks import run_component_checks, serialize_checks, summarise_results

router = APIRouter(tags=["health"], prefix="/api")


@router.get("/health")
async def health(request: Request, strict: bool = Query(False, description="HTTP 503 если есть 'fail'")):
    results = await run_component_checks(request.app)
    overall, fail_count = summarise_results(results)
    status_code = status.HTTP_200_OK if fail_count == 0 else status.HTTP_503_SERVICE_UNAVAILABLE
    if strict and overall != "ok":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    payload: Dict[str, object] = {
        "status": overall,
        "checks": serialize_checks(results),
        "version": os.getenv("APP_VERSION"),
    }
    return JSONResponse(status_code=status_code, content=payload)


@router.get("/healthz", response_class=Response)
async def healthz() -> Response:
    return Response(content="ok", media_type="text/plain", status_code=status.HTTP_200_OK)
