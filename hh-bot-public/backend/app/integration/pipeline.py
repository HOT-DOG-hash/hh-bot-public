from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from .ingest import PartnerIngestLogRepository, PartnerIngestService
from .models import IdempotencyMismatchError, NormalizedPartnerEvent, PartnerRawEvent
from .normalizer import normalize_event
from .storage import PartnerStorageGateway, StorageOutcome
from .validator import ValidationResult, validate_event


@dataclass
class PipelineResult:
    status: str
    raw_event: Optional[PartnerRawEvent] = None
    normalized_event: Optional[NormalizedPartnerEvent] = None
    validation: Optional[ValidationResult] = None
    storage: Optional[StorageOutcome] = None
    message: Optional[str] = None


class PartnerIntegrationPipeline:
    """High-level coordinator for partner ingestion stages."""

    def __init__(
        self,
        *,
        ingest_service: Optional[PartnerIngestService] = None,
        storage_gateway: Optional[PartnerStorageGateway] = None,
    ) -> None:
        self._ingest_service = ingest_service or PartnerIngestService()
        self._storage_gateway = storage_gateway or PartnerStorageGateway()

    @property
    def ingest_log(self) -> PartnerIngestLogRepository:
        return self._ingest_service.log_repository

    @property
    def storage_gateway(self) -> PartnerStorageGateway:
        return self._storage_gateway

    def process(
        self,
        *,
        partner_code: str,
        external_id: str,
        payload: Dict[str, Any],
        received_at: Optional[datetime] = None,
        endpoint: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> PipelineResult:
        try:
            raw_event = self._ingest_service.record_raw_event(
                partner_code=partner_code,
                external_id=external_id,
                payload=payload,
                received_at=received_at,
                endpoint=endpoint,
                request_id=request_id,
            )
        except IdempotencyMismatchError as exc:  # pragma: no cover - orchestration path
            return PipelineResult(status="idempotency_conflict", message=str(exc))

        if raw_event is None:
            return PipelineResult(status="duplicate")

        normalized_event = normalize_event(raw_event)
        validation = validate_event(normalized_event)

        self._storage_gateway.write_to_staging(normalized_event, validation_passed=validation.passed)

        ingest_key = str(raw_event.ingest_key)
        if not validation.passed:
            self.ingest_log.mark_status(partner_code, ingest_key, status="failed", error_reason="validation")
            return PipelineResult(
                status="validation_failed",
                raw_event=raw_event,
                normalized_event=normalized_event,
                validation=validation,
            )

        outcome = self._storage_gateway.promote_to_core(normalized_event)
        self.ingest_log.mark_status(partner_code, ingest_key, status="processed", error_reason=None)

        return PipelineResult(
            status="stored" if outcome.inserted or outcome.updated else "no_change",
            raw_event=raw_event,
            normalized_event=normalized_event,
            validation=validation,
            storage=outcome,
        )
