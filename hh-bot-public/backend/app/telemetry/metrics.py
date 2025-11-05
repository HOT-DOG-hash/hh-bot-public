from __future__ import annotations

from time import perf_counter
from typing import Callable, Dict, Iterator, Optional

try:
    from prometheus_client import Counter, Gauge, Histogram
except ModuleNotFoundError:  # pragma: no cover
    from backend.app.telemetry.prometheus_stub import Counter, Gauge, Histogram

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.auto_campaigns import (
    Campaign,
    CampaignCompanyBlacklist,
    CampaignMode,
    CampaignNotificationChannel,
    CampaignStatus,
    DeliveryLogStatus,
)
_created_total = Counter("campaign_created_total", "Total number of auto campaigns created", ("mode",))

_state_transitions_total = Counter(
    "campaign_state_transitions_total",
    "Campaign state transitions",
    ("from_state", "to_state"),
)

_idempotency_conflicts_total = Counter(
    "campaign_idempotency_conflicts_total",
    "Number of idempotency conflicts detected for auto campaign operations",
    ("endpoint",),
)

_auto_pauses_total = Counter(
    "campaign_auto_pauses_total",
    "Number of automatic pauses triggered for campaigns",
    ("reason",),
)

_delivery_logs_total = Counter(
    "campaign_delivery_logs_total",
    "Delivery log outcomes per campaign",
    ("result",),
)

_campaign_runs_total = Counter(
    "campaign_runs_total",
    "Total number of campaign runs executed",
    ("campaign_id", "mode"),
)

_campaign_run_duration_seconds = Histogram(
    "campaign_run_duration_seconds",
    "Duration of campaign runs in seconds",
    ("campaign_id",),
    buckets=(5, 10, 30, 60, 120, 300, 600, 900, 1800),
)

_campaign_delay_applied_ms = Gauge(
    "campaign_delay_applied_ms",
    "Adaptive delay/backoff currently applied to campaign runs",
    ("campaign_id",),
)

_campaign_notifications_sent_total = Counter(
    "campaign_notifications_sent_total",
    "Campaign notification send outcomes",
    ("campaign_id", "channel", "status"),
)

_applications_skipped_total = Counter(
    "applications_skipped_total",
    "Applications skipped by campaigns",
    ("campaign_id", "reason", "origin"),
)

_delivery_window_backoff_seconds = Histogram(
    "delivery_window_backoff_seconds",
    "Observed backoff interval between campaign delivery windows",
    ("campaign_id",),
    buckets=(5, 10, 30, 60, 120, 300, 600, 900, 1800),
)

_delivery_notification_latency_seconds = Histogram(
    "delivery_notification_latency_seconds",
    "Latency between event creation and notification delivery",
    ("campaign_id", "channel"),
    buckets=(0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600, 900),
)

_campaign_blacklist_size = Gauge(
    "campaign_blacklist_size",
    "Current size of campaign blacklist per owner",
    ("owner_id",),
)

_partner_ingest_total = Counter(
    "partner_ingest_total",
    "Total partner requests by endpoint",
    ("partner", "endpoint"),
)

_partner_ingest_errors_total = Counter(
    "partner_ingest_errors_total",
    "Partner pipeline errors by endpoint and code",
    ("partner", "endpoint", "code"),
)

_partner_dedup_total = Counter(
    "partner_dedup_total",
    "Partner pipeline deduplication hits",
    ("partner", "reason"),
)

_partner_latency_seconds = Histogram(
    "partner_latency_seconds",
    "Partner API or pipeline latency seconds",
    ("partner", "endpoint"),
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30),
)

_partner_quota_remaining = Gauge(
    "partner_quota_remaining",
    "Remaining partner quota units",
    ("partner", "window"),
)

_partner_payload_size_bytes = Histogram(
    "partner_payload_size_bytes",
    "Partner payload size bytes",
    ("partner", "endpoint"),
    buckets=(256, 512, 1024, 2048, 4096, 8192, 16384, 65536, 131072),
)

_integration_validation_failures_total = Counter(
    "integration_validation_failures_total",
    "Partner validation failures",
    ("partner", "code"),
)

_delivery_attempt_errors = Counter(
    "delivery_attempt_errors_total",
    "Count of delivery attempt errors for auto campaigns",
    ("type",),
)

_scheduler_lag_seconds = Gauge(
    "campaign_scheduler_lag_seconds",
    "Scheduler lag seconds for auto campaigns",
    ("partition",),
)

_campaign_ready_state = Gauge(
    "campaign_ready_state",
    "Readiness state of auto campaign dependencies (1=ready,0=fail)",
    ("component",),
)

_campaign_active_total = Gauge(
    "campaign_active_total",
    "Current number of active auto campaigns by mode",
    ("mode",),
)

_operation_latency_seconds = Histogram(
    "campaign_operation_latency_seconds",
    "Latency of auto campaign operations",
    ("operation",),
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)


_active_counts: Dict[CampaignMode, int] = {mode: 0 for mode in CampaignMode}
_scheduler_lag_latest: Dict[str, float] = {}
_READY_COMPONENTS = ("db", "redis", "scheduler", "feature_flag", "idempotency_store")

for _component in _READY_COMPONENTS:
    # Initialise labelset so metrics scrape shows all components even before checks run.
    _campaign_ready_state.labels(component=_component).set(0.0)


def _set_active_count(mode: CampaignMode, value: int) -> None:
    safe_value = max(0, int(value))
    _active_counts[mode] = safe_value
    _campaign_active_total.labels(mode=mode.value).set(safe_value)


def record_campaign_created(mode: CampaignMode) -> None:
    _created_total.labels(mode=mode.value).inc()


def record_state_transition(previous: CampaignStatus, new: CampaignStatus, *, mode: CampaignMode) -> None:
    if previous is new:
        return
    _state_transitions_total.labels(from_state=previous.value, to_state=new.value).inc()
    if previous is CampaignStatus.ACTIVE:
        _set_active_count(mode, _active_counts.get(mode, 0) - 1)
    if new is CampaignStatus.ACTIVE:
        _set_active_count(mode, _active_counts.get(mode, 0) + 1)


def record_idempotency_conflict(endpoint: str) -> None:
    _idempotency_conflicts_total.labels(endpoint=endpoint).inc()


def record_auto_pause(reason: str) -> None:
    _auto_pauses_total.labels(reason=reason).inc()


def record_delivery_log(result: DeliveryLogStatus) -> None:
    _delivery_logs_total.labels(result=result.value).inc()


def record_delivery_error(error_type: str) -> None:
    _delivery_attempt_errors.labels(type=error_type).inc()


def record_campaign_run(campaign_id: int, mode: CampaignMode) -> None:
    _campaign_runs_total.labels(campaign_id=str(campaign_id), mode=mode.value).inc()


def observe_campaign_run_duration(campaign_id: int, seconds: float) -> None:
    _campaign_run_duration_seconds.labels(campaign_id=str(campaign_id)).observe(max(seconds, 0.0))


def set_campaign_delay_ms(campaign_id: int, delay_ms: Optional[float]) -> None:
    value = 0.0 if delay_ms is None else max(float(delay_ms), 0.0)
    _campaign_delay_applied_ms.labels(campaign_id=str(campaign_id)).set(value)


def record_notification_sent(
    campaign_id: int,
    channel: CampaignNotificationChannel | str,
    status: str,
) -> None:
    _campaign_notifications_sent_total.labels(
        campaign_id=str(campaign_id),
        channel=(channel.value if isinstance(channel, CampaignNotificationChannel) else str(channel).lower()),
        status=status.lower(),
    ).inc()


def record_application_skipped(campaign_id: int, reason: str, origin: str) -> None:
    _applications_skipped_total.labels(
        campaign_id=str(campaign_id),
        reason=reason.lower(),
        origin=origin.lower(),
    ).inc()


def observe_delivery_backoff(campaign_id: int, seconds: float) -> None:
    _delivery_window_backoff_seconds.labels(campaign_id=str(campaign_id)).observe(max(seconds, 0.0))


def observe_notification_latency(campaign_id: int, channel: str, seconds: float) -> None:
    _delivery_notification_latency_seconds.labels(
        campaign_id=str(campaign_id),
        channel=str(channel).lower(),
    ).observe(max(seconds, 0.0))


def set_blacklist_size(owner_id: int, size: int) -> None:
    _campaign_blacklist_size.labels(owner_id=str(owner_id)).set(max(size, 0))


def record_partner_request(partner: str, endpoint: str) -> None:
    _partner_ingest_total.labels(partner=partner, endpoint=endpoint).inc()


def record_partner_error(partner: str, endpoint: str, code: str) -> None:
    _partner_ingest_errors_total.labels(partner=partner, endpoint=endpoint, code=code).inc()


def record_partner_dedup(partner: str, reason: str) -> None:
    _partner_dedup_total.labels(partner=partner, reason=reason).inc()


def observe_partner_latency(partner: str, endpoint: str, seconds: float) -> None:
    _partner_latency_seconds.labels(partner=partner, endpoint=endpoint).observe(max(seconds, 0.0))


def set_partner_quota(partner: str, window: str, remaining: float) -> None:
    _partner_quota_remaining.labels(partner=partner, window=window).set(remaining)


def observe_partner_payload_size(partner: str, endpoint: str, size_bytes: int) -> None:
    _partner_payload_size_bytes.labels(partner=partner, endpoint=endpoint).observe(max(size_bytes, 0))


def record_validation_failure(partner: str, code: str) -> None:
    _integration_validation_failures_total.labels(partner=partner, code=code).inc()


def set_scheduler_lag(seconds: float, partition: str = "default") -> None:
    value = max(seconds, 0.0)
    _scheduler_lag_seconds.labels(partition=partition).set(value)
    _scheduler_lag_latest[partition] = value


def get_scheduler_lag(partition: str = "default") -> Optional[float]:
    return _scheduler_lag_latest.get(partition)


def set_component_ready_state(component: str, ready: bool) -> None:
    value = 1.0 if ready else 0.0
    _campaign_ready_state.labels(component=component).set(value)


def observe_operation_latency(operation: str, seconds: float) -> None:
    _operation_latency_seconds.labels(operation=operation).observe(max(seconds, 0.0))


def track_operation_latency(operation: str) -> Callable[[Callable[..., Iterator]], Callable[..., Iterator]]:
    """
    Decorator for synchronous contexts to measure latency.

    Designed for small helper functions inside services.
    """

    def decorator(func: Callable[..., Iterator]):
        def wrapper(*args, **kwargs):
            start = perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                observe_operation_latency(operation, perf_counter() - start)

        return wrapper

    return decorator


async def hydrate_active_campaigns(session: AsyncSession) -> None:
    """
    Refresh in-memory counters backing `campaign_active_total` from the database.
    Ensures gauges remain accurate across process restarts.
    """

    for mode in CampaignMode:
        _set_active_count(mode, 0)

    result = await session.execute(
        select(Campaign.mode, func.count())
        .where(Campaign.status == CampaignStatus.ACTIVE)
        .group_by(Campaign.mode)
    )
    for mode, total in result.all():
        _set_active_count(mode, total)

    blacklist_result = await session.execute(
        select(CampaignCompanyBlacklist.owner_id, func.count())
        .where(CampaignCompanyBlacklist.removed_at.is_(None))
        .group_by(CampaignCompanyBlacklist.owner_id)
    )
    for owner_id, total in blacklist_result.all():
        set_blacklist_size(owner_id, total)

