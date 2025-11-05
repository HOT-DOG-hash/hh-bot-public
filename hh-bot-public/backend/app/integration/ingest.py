from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Dict, Optional, Tuple

from backend.app.telemetry.metrics import (
    observe_partner_latency,
    observe_partner_payload_size,
    record_partner_dedup,
    record_partner_error,
    record_partner_request,
    set_partner_quota,
)

from .models import (
    IdempotencyMismatchError,
    PartnerIngestLogEntry,
    PartnerRawEvent,
    build_ingest_key,
    hash_payload,
)


class PartnerIngestLogRepository:
    """In-memory repository that represents the future `partner_ingest_log` table."""

    def __init__(self) -> None:
        self._storage: Dict[Tuple[str, str], PartnerIngestLogEntry] = {}

    def get(self, partner_code: str, ingest_key: str) -> Optional[PartnerIngestLogEntry]:
        return self._storage.get((partner_code, ingest_key))

    def upsert(self, entry: PartnerIngestLogEntry) -> PartnerIngestLogEntry:
        self._storage[(entry.partner_code, str(entry.ingest_key))] = entry
        return entry

    def mark_status(
        self,
        partner_code: str,
        ingest_key: str,
        *,
        status: str,
        error_reason: Optional[str] = None,
    ) -> Optional[PartnerIngestLogEntry]:
        entry = self._storage.get((partner_code, ingest_key))
        if entry is None:
            return None
        entry.status = status
        entry.error_reason = error_reason
        return entry


class PartnerIngestService:
    """Skeleton ingest stage responsible for idempotency and raw event persistence."""

    def __init__(self, log_repository: Optional[PartnerIngestLogRepository] = None) -> None:
        self._log_repository = log_repository or PartnerIngestLogRepository()

    @property
    def log_repository(self) -> PartnerIngestLogRepository:
        return self._log_repository

    def record_raw_event(
        self,
        *,
        partner_code: str,
        external_id: str,
        payload: Dict[str, object],
        received_at: Optional[datetime] = None,
        endpoint: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Optional[PartnerRawEvent]:
        """
        Register the incoming payload, enforcing idempotency on an hourly bucket.

        Returns a PartnerRawEvent when the payload should continue to downstream
        processing. If the payload is a duplicate (same idempotency key and hash),
        None is returned to signal no-op processing.
        """

        endpoint_label = endpoint or "unknown"
        stage_started = perf_counter()

        received = received_at or datetime.now(timezone.utc)
        ingest_key, ts_hour = build_ingest_key(partner_code, external_id, received)
        payload_hash, payload_bytes = hash_payload(payload, include_bytes=True)
        observe_partner_payload_size(partner_code, endpoint_label, len(payload_bytes))
        record_partner_request(partner_code, endpoint_label)

        quota_info = payload.get("quota") or payload.get("details")
        if isinstance(quota_info, dict):
            remaining = quota_info.get("remaining")
            if remaining is None and all(k in quota_info for k in ("limit", "used")):
                try:
                    remaining = float(quota_info["limit"]) - float(quota_info["used"])
                except (TypeError, ValueError):
                    remaining = None
            window = quota_info.get("window")
            window_seconds = quota_info.get("window_seconds")
            window_label = None
            if isinstance(window, str) and window:
                window_label = window
            elif window_seconds is not None:
                window_label = f"{window_seconds}s"
            if remaining is not None and window_label:
                try:
                    set_partner_quota(partner_code, window_label, float(remaining))
                except (TypeError, ValueError):
                    pass

        existing = self._log_repository.get(partner_code, str(ingest_key))
        if existing:
            if existing.hash_payload == payload_hash:
                record_partner_dedup(partner_code, "hard_key")
                self._log_repository.mark_status(
                    partner_code,
                    str(ingest_key),
                    status="duplicate",
                    error_reason=None,
                )
                return None
            record_partner_error(partner_code, endpoint_label, "payload_conflict")
            self._log_repository.mark_status(
                partner_code,
                str(ingest_key),
                status="failed",
                error_reason="payload_conflict",
            )
            raise IdempotencyMismatchError(
                message="Incoming payload conflicts with previously ingested payload.",
                partner_code=partner_code,
                external_id=external_id,
                ingest_key=ingest_key,
                existing_hash=existing.hash_payload,
                incoming_hash=payload_hash,
            )

        log_entry = PartnerIngestLogEntry(
            partner_code=partner_code,
            external_id=external_id,
            ingest_key=ingest_key,
            hash_payload=payload_hash,
            ingested_at=received,
            status="processed",
            error_reason=None,
            endpoint=endpoint,
            request_id=request_id,
        )
        self._log_repository.upsert(log_entry)
        observe_partner_latency(partner_code, endpoint_label, perf_counter() - stage_started)

        return PartnerRawEvent(
            partner_code=partner_code,
            external_id=external_id,
            payload=payload,
            received_at=received,
            endpoint=endpoint,
            request_id=request_id,
            ingest_key=ingest_key,
            hash_payload=payload_hash,
            ts_hour=ts_hour,
        )
