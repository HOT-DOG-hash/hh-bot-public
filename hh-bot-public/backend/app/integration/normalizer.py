from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Dict, Optional

from backend.app.telemetry.metrics import observe_partner_latency

from .models import NormalizedPartnerEvent, PartnerRawEvent


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        cleaned = value.replace("Z", "+00:00") if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(cleaned)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def _normalize_currency(currency: Optional[str]) -> Optional[str]:
    if not currency:
        return None
    trimmed = currency.strip().upper()
    if len(trimmed) != 3:
        return None
    return trimmed


def _convert_salary_minor(payload: Dict[str, Any]) -> tuple[Optional[int], Optional[str], Optional[float]]:
    salary_block = payload.get("salary") or {}
    currency = _normalize_currency(salary_block.get("currency"))
    amount = salary_block.get("amount_minor")
    if amount is None:
        minimum = salary_block.get("min")
        maximum = salary_block.get("max")
        if minimum is None and maximum is None:
            return None, currency, None
        numeric_values = [value for value in (minimum, maximum) if isinstance(value, (int, float))]
        if not numeric_values:
            return None, currency, None
        average = sum(numeric_values) / len(numeric_values)
        amount = int(average * 100)
    if isinstance(amount, float):
        amount = int(amount)
    rate = salary_block.get("currency_rate")
    try:
        rate_value = float(rate) if rate is not None else None
    except (TypeError, ValueError):
        rate_value = None
    return int(amount) if isinstance(amount, int) else None, currency, rate_value


def _normalize_location(payload: Dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    location = payload.get("location") or {}
    country = location.get("country")
    region = location.get("region")
    city = location.get("city")
    return (
        country.strip().upper() if isinstance(country, str) and len(country.strip()) == 2 else None,
        region.strip() if isinstance(region, str) else None,
        city.strip() if isinstance(city, str) else None,
    )


def _detect_language(partner_code: str, payload: Dict[str, Any]) -> Optional[str]:
    language = payload.get("language") or payload.get("locale")
    if isinstance(language, str):
        return language.split("_", 1)[0].lower()
    if partner_code.startswith("hh"):
        return "ru"
    if partner_code.startswith("habr"):
        return "ru"
    return "en"


def normalize_event(raw: PartnerRawEvent) -> NormalizedPartnerEvent:
    """
    Normalize raw partner payload into the unified schema described in integration/SCHEMAS.md.
    """

    stage_started = perf_counter()
    normalized_at = datetime.now(timezone.utc)
    sent_at = (
        _parse_timestamp(raw.payload.get("sent_at"))
        or _parse_timestamp(raw.payload.get("created_at"))
        or raw.received_at
    )
    updated_at = _parse_timestamp(raw.payload.get("updated_at") or raw.payload.get("updated_at_partner"))
    vacancy_id = raw.payload.get("vacancy_id") or raw.payload.get("vacancy", {}).get("id") or raw.payload.get("job", {}).get("id")
    company = raw.payload.get("company") or raw.payload.get("employer") or {}
    company_id = company.get("id") or company.get("external_id")

    salary_minor, currency, salary_rate = _convert_salary_minor(raw.payload)
    country, region, city = _normalize_location(raw.payload)
    status = str(raw.payload.get("status") or raw.payload.get("state") or "unknown").lower()

    normalized = NormalizedPartnerEvent(
        partner_code=raw.partner_code,
        external_id=raw.external_id,
        vacancy_id=str(vacancy_id) if vacancy_id is not None else None,
        company_id=str(company_id) if company_id is not None else None,
        status=status,
        sent_at=sent_at,
        updated_at=updated_at,
        language=_detect_language(raw.partner_code, raw.payload),
        salary_minor=salary_minor,
        currency=currency,
        salary_currency_rate=salary_rate,
        location_country=country,
        location_region=region,
        location_city=city,
        ingest_key=raw.ingest_key,
        ingested_at=raw.received_at,
        normalized_at=normalized_at,
        raw_payload=raw.payload,
        metadata={
            "ts_hour": raw.ts_hour.isoformat(),
            "payload_hash": raw.hash_payload,
        },
    )

    observe_partner_latency(
        raw.partner_code,
        "normalize",
        perf_counter() - stage_started,
    )
    return normalized
