from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Optional, Tuple


def truncate_to_hour(moment: datetime) -> datetime:
    """Return the timestamp rounded down to the start of the hour in UTC."""
    return moment.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def build_ingest_key(partner_code: str, external_id: str, received_at: datetime) -> tuple[uuid.UUID, datetime]:
    """
    Build the deterministic ingest key based on (partner_code, external_id, ts_hour).

    The key is represented as UUIDv5 so it can be stored in the schema defined
    in integration/SCHEMAS.md.
    """
    ts_hour = truncate_to_hour(received_at)
    key_source = f"{partner_code}:{external_id}:{ts_hour.isoformat()}"
    ingest_key = uuid.uuid5(uuid.NAMESPACE_URL, key_source)
    return ingest_key, ts_hour


def hash_payload(payload: Dict[str, Any], *, include_bytes: bool = False) -> str | Tuple[str, bytes]:
    """Stable SHA256 hash of the payload used for idempotency and auditing."""
    payload_dump = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    digest = sha256(payload_dump).hexdigest()
    if include_bytes:
        return digest, payload_dump
    return digest


@dataclass(frozen=True)
class PartnerPipelineError(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover - repr convenience
        return self.message


@dataclass(frozen=True)
class IdempotencyMismatchError(PartnerPipelineError):
    partner_code: str
    external_id: str
    ingest_key: uuid.UUID
    existing_hash: str
    incoming_hash: str


@dataclass(frozen=True)
class PartnerRawEvent:
    partner_code: str
    external_id: str
    payload: Dict[str, Any]
    received_at: datetime
    endpoint: Optional[str]
    request_id: Optional[str]
    ingest_key: uuid.UUID
    hash_payload: str
    ts_hour: datetime


@dataclass(frozen=True)
class NormalizedPartnerEvent:
    partner_code: str
    external_id: str
    vacancy_id: Optional[str]
    company_id: Optional[str]
    status: str
    sent_at: datetime
    updated_at: Optional[datetime]
    language: Optional[str]
    salary_minor: Optional[int]
    currency: Optional[str]
    salary_currency_rate: Optional[float]
    location_country: Optional[str]
    location_region: Optional[str]
    location_city: Optional[str]
    ingest_key: uuid.UUID
    ingested_at: datetime
    normalized_at: datetime
    raw_payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str
    code: str = "invalid"


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    issues: List[ValidationIssue] = field(default_factory=list)


@dataclass
class PartnerIngestLogEntry:
    partner_code: str
    external_id: str
    ingest_key: uuid.UUID
    hash_payload: str
    ingested_at: datetime
    status: str
    error_reason: Optional[str] = None
    endpoint: Optional[str] = None
    request_id: Optional[str] = None
