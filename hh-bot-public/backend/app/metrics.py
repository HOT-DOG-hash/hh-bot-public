from __future__ import annotations

from typing import Optional

try:
    from prometheus_client import Counter, Gauge, Histogram
except ModuleNotFoundError:  # pragma: no cover
    from backend.app.telemetry.prometheus_stub import Counter, Gauge, Histogram


_PAYMENTS_INITIATED = Counter(
    "payments_initiated_total",
    "Total number of initiated payments",
    ("plan_code",),
)
_PAYMENTS_SUCCEEDED = Counter("payments_succeeded_total", "Total number of succeeded payments", ("plan_code",))
_PAYMENTS_FAILED = Counter(
    "payments_failed_total",
    "Total number of failed payments",
    ("plan_code", "reason"),
)
_PAYMENTS_REVENUE_MINOR = Counter(
    "payments_revenue_minor_total",
    "Total captured payment volume in minor currency units",
    ("plan_code",),
)
_PAYMENTS_REFUNDS_MINOR = Counter(
    "payments_refunds_minor_total",
    "Total refunded payment volume in minor currency units",
    ("plan_code",),
)
_WEBHOOK_LAG_SECONDS = Histogram(
    "webhook_lag_seconds",
    "Time between provider event creation and webhook processing",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600),
)
_APPLICATIONS_SENT = Counter(
    "applications_sent_total",
    "Total number of applications sent via the bot",
    ("plan_code",),
)
_DAILY_QUOTA_REMAINING = Gauge(
    "daily_quota_remaining",
    "Remaining daily quota per plan",
    ("plan_code",),
)


def _plan_label(plan_code: Optional[str]) -> str:
    return (plan_code or "unknown").upper()


def observe_payment_initiated(plan_code: str) -> None:
    label = _plan_label(plan_code)
    _PAYMENTS_INITIATED.labels(plan_code=label).inc()
    _PAYMENTS_REVENUE_MINOR.labels(plan_code=label).inc(0)
    _PAYMENTS_REFUNDS_MINOR.labels(plan_code=label).inc(0)


def observe_payment_succeeded(plan_code: str, amount_minor: int) -> None:
    label = _plan_label(plan_code)
    _PAYMENTS_SUCCEEDED.labels(plan_code=label).inc()
    _PAYMENTS_REVENUE_MINOR.labels(plan_code=label).inc(max(int(amount_minor), 0))
    _PAYMENTS_REFUNDS_MINOR.labels(plan_code=label).inc(0)


def observe_payment_failed(plan_code: str, reason: str, refund_minor: int = 0) -> None:
    label = _plan_label(plan_code)
    _PAYMENTS_FAILED.labels(plan_code=label, reason=reason).inc()
    if refund_minor:
        _PAYMENTS_REFUNDS_MINOR.labels(plan_code=label).inc(max(int(refund_minor), 0))
    else:
        _PAYMENTS_REFUNDS_MINOR.labels(plan_code=label).inc(0)


def observe_webhook_lag(seconds: Optional[float]) -> None:
    if seconds is None:
        return
    if seconds < 0:
        seconds = 0
    _WEBHOOK_LAG_SECONDS.observe(seconds)


def observe_applications_sent(plan_code: Optional[str], count: int) -> None:
    _APPLICATIONS_SENT.labels(plan_code=_plan_label(plan_code)).inc(count)


def set_daily_quota_remaining(plan_code: Optional[str], remaining: int) -> None:
    _DAILY_QUOTA_REMAINING.labels(plan_code=_plan_label(plan_code)).set(max(remaining, 0))
