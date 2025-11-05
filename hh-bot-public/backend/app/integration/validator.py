from __future__ import annotations

from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import List

from backend.app.telemetry.metrics import (
    observe_partner_latency,
    record_partner_error,
    record_validation_failure,
)

from .models import NormalizedPartnerEvent, ValidationIssue, ValidationResult

_ALLOWED_STATUSES = {"sent", "failed", "skipped", "accepted", "viewed"}


def _collect_required_fields(event: NormalizedPartnerEvent) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not event.external_id:
        issues.append(ValidationIssue(field="external_id", message="external_id is required"))
    if not event.vacancy_id:
        issues.append(ValidationIssue(field="vacancy_id", message="vacancy_id is required"))
    if not event.status:
        issues.append(ValidationIssue(field="status", message="status is required"))
    if event.sent_at is None:
        issues.append(ValidationIssue(field="sent_at", message="sent_at is required"))
    return issues


def validate_event(event: NormalizedPartnerEvent) -> ValidationResult:
    """Validate normalized partner event per integration/PIPELINE.md requirements."""

    stage_started = perf_counter()

    issues = _collect_required_fields(event)

    if event.status and event.status not in _ALLOWED_STATUSES:
        issues.append(
            ValidationIssue(
                field="status",
                message=f"status '{event.status}' is not allowed",
                code="invalid_status",
            )
        )

    if event.sent_at:
        future_cutoff = datetime.now(timezone.utc) + timedelta(minutes=5)
        if event.sent_at > future_cutoff:
            issues.append(
                ValidationIssue(
                    field="sent_at",
                    message="sent_at is in the future beyond allowed window",
                    code="timestamp_future",
                )
            )

    if event.salary_minor is not None and event.salary_minor < 0:
        issues.append(
            ValidationIssue(
                field="salary_minor",
                message="salary_minor must be >= 0",
                code="invalid_salary",
            )
        )

    passed = len(issues) == 0
    if not passed:
        for issue in issues:
            record_validation_failure(event.partner_code, issue.code)
            record_partner_error(event.partner_code, "validate", issue.code)

    observe_partner_latency(
        event.partner_code,
        "validate",
        perf_counter() - stage_started,
    )
    return ValidationResult(passed=passed, issues=issues)
