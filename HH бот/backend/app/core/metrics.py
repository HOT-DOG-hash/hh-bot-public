from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class _LabelSet:
    metric: _BaseMetric
    key: tuple[Any, ...]

    def inc(self, amount: int = 1) -> None:
        self.metric._values[self.key] += amount

    def observe(self, value: float) -> None:
        self.metric._values[self.key].append(float(value))


class _BaseMetric:
    def __init__(self, name: str, label_names: Iterable[str]):
        self.name = name
        self.label_names = tuple(label_names)
        self._values: Any = None

    def labels(self, **labels: Any) -> _LabelSet:
        if set(labels) != set(self.label_names):  # pragma: no cover - defensive
            missing = set(self.label_names) - set(labels)
            extra = set(labels) - set(self.label_names)
            parts = []
            if missing:
                parts.append(f"missing labels: {sorted(missing)}")
            if extra:
                parts.append(f"unknown labels: {sorted(extra)}")
            raise ValueError(f"Invalid labels for {self.name}: {'; '.join(parts)}")
        key = tuple(labels[name] for name in self.label_names)
        return _LabelSet(self, key)


class Counter(_BaseMetric):
    def __init__(self, name: str, label_names: Iterable[str] = ()):  # noqa: D401 - simple
        super().__init__(name, label_names)
        self._values = defaultdict(int)

    def inc(self, amount: int = 1, **labels: Any) -> None:
        self.labels(**labels).inc(amount)

    def value(self, **labels: Any) -> int:
        key = tuple(labels[name] for name in self.label_names)
        return self._values.get(key, 0)


class Histogram(_BaseMetric):
    def __init__(self, name: str, label_names: Iterable[str] = ()):  # noqa: D401
        super().__init__(name, label_names)
        self._values = defaultdict(list)

    def observe(self, value: float, **labels: Any) -> None:
        self.labels(**labels).observe(value)


payments_initiated_total = Counter("payments_initiated_total", ("plan_code",))
payment_webhooks_total = Counter("payment_webhooks_total", ("event_type",))
payments_status_total = Counter("payments_status_total", ("status",))
yoomoney_api_latency_ms = Histogram("yoomoney_api_latency_ms", ("action",))
webhook_processing_ms = Histogram("webhook_processing_ms", ("result",))

__all__ = [
    "Counter",
    "Histogram",
    "payment_webhooks_total",
    "payments_initiated_total",
    "payments_status_total",
    "webhook_processing_ms",
    "yoomoney_api_latency_ms",
]
