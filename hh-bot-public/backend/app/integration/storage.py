from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Dict, Optional, Tuple

from backend.app.telemetry.metrics import observe_partner_latency, record_partner_dedup

from .models import NormalizedPartnerEvent


@dataclass
class StorageOutcome:
    partner_code: str
    external_id: str
    inserted: bool
    updated: bool
    reason: Optional[str] = None


class PartnerStorageGateway:
    """In-memory storage gateway mirroring staging → core flow."""

    def __init__(self) -> None:
        self._staging_records: list[dict] = []
        self._core_records: Dict[Tuple[str, str], dict] = {}

    @property
    def staging_records(self) -> list[dict]:
        return self._staging_records

    @property
    def core_records(self) -> Dict[Tuple[str, str], dict]:
        return self._core_records

    def write_to_staging(self, event: NormalizedPartnerEvent, *, validation_passed: bool) -> None:
        self._staging_records.append(
            {
                "partner_code": event.partner_code,
                "external_id": event.external_id,
                "ingest_key": str(event.ingest_key),
                "payload_hash": event.metadata.get("payload_hash"),
                "ingested_at": event.ingested_at,
                "normalized_at": event.normalized_at,
                "validation_status": "passed" if validation_passed else "failed",
            }
        )

    def promote_to_core(self, event: NormalizedPartnerEvent) -> StorageOutcome:
        stage_started = perf_counter()

        key = (event.partner_code, event.external_id)
        existing = self._core_records.get(key)

        if existing and existing.get("status") == event.status:
            record_partner_dedup(event.partner_code, "status_same")
            observe_partner_latency(event.partner_code, "store", perf_counter() - stage_started)
            return StorageOutcome(
                partner_code=event.partner_code,
                external_id=event.external_id,
                inserted=False,
                updated=False,
                reason="unchanged_status",
            )

        payload = {
            "partner_code": event.partner_code,
            "external_id": event.external_id,
            "status": event.status,
            "sent_at": event.sent_at,
            "ingested_at": event.ingested_at,
            "normalized_at": event.normalized_at,
            "salary_minor": event.salary_minor,
            "currency": event.currency,
            "location_country": event.location_country,
            "location_region": event.location_region,
            "location_city": event.location_city,
            "metadata": event.metadata,
        }
        self._core_records[key] = payload

        observe_partner_latency(event.partner_code, "store", perf_counter() - stage_started)

        return StorageOutcome(
            partner_code=event.partner_code,
            external_id=event.external_id,
            inserted=existing is None,
            updated=existing is not None,
            reason=None if existing is None else "status_changed",
        )
