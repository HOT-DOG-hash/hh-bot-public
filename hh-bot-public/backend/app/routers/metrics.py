from __future__ import annotations

from fastapi import APIRouter, Response

try:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
except ModuleNotFoundError:  # pragma: no cover
    from backend.app.telemetry.prometheus_stub import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter()


@router.get("/metrics")
def metrics_endpoint() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
