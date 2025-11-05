from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"


@dataclass
class _CounterCell:
    value: float = 0.0

    def inc(self, amount: float = 1.0) -> None:
        self.value += amount


@dataclass
class _GaugeCell:
    value: float = 0.0

    def inc(self, amount: float = 1.0) -> None:
        self.value += amount

    def set(self, value: float) -> None:
        self.value = value


@dataclass
class _HistogramCell:
    count: int = 0
    total: float = 0.0

    def observe(self, value: float) -> None:
        self.count += 1
        self.total += value


class _MetricBase:
    _registry: Dict[str, "_MetricBase"] = {}

    def __init__(self, name: str, documentation: str, labelnames: Iterable[str] = ()):
        self.name = name
        self.documentation = documentation
        self.labelnames = tuple(labelnames)
        self._samples: Dict[Tuple[str, ...], object] = {}
        _MetricBase._registry[name] = self

    def labels(self, **labels: str):
        key = tuple(labels.get(l, "") for l in self.labelnames)
        if len(key) != len(self.labelnames):
            raise ValueError("label mismatch for metric %s" % self.name)
        if key not in self._samples:
            self._samples[key] = self._create_cell()
        return self._samples[key]

    @classmethod
    def registry(cls) -> Iterable["_MetricBase"]:
        return cls._registry.values()

    def _create_cell(self):
        raise NotImplementedError

    @property
    def metric_type(self) -> str:
        raise NotImplementedError


class Counter(_MetricBase):
    def _create_cell(self) -> _CounterCell:
        return _CounterCell()

    @property
    def metric_type(self) -> str:
        return "counter"


class Gauge(_MetricBase):
    def _create_cell(self) -> _GaugeCell:
        return _GaugeCell()

    @property
    def metric_type(self) -> str:
        return "gauge"


class Histogram(_MetricBase):
    def __init__(self, name: str, documentation: str, labelnames: Iterable[str] = (), buckets: Iterable[float] | None = None):
        super().__init__(name, documentation, labelnames)
        self._buckets = list(buckets or ())

    def _create_cell(self) -> _HistogramCell:
        return _HistogramCell()

    @property
    def metric_type(self) -> str:
        return "histogram"

    def observe(self, value: float) -> None:
        self.labels().observe(value)


def generate_latest() -> bytes:
    lines: list[str] = []
    for metric in _MetricBase.registry():
        lines.append(f"# HELP {metric.name} {metric.documentation}")
        lines.append(f"# TYPE {metric.name} {metric.metric_type}")
        for labels, cell in metric._samples.items():
            label_str = ""
            if metric.labelnames:
                pairs = [f'{name}="{value}"' for name, value in zip(metric.labelnames, labels)]
                label_str = "{" + ",".join(pairs) + "}"
            if isinstance(cell, _CounterCell):
                value = cell.value
            elif isinstance(cell, _GaugeCell):
                value = cell.value
            elif isinstance(cell, _HistogramCell):
                value = cell.total
            else:  # pragma: no cover - defensive
                value = 0
            lines.append(f"{metric.name}{label_str} {value}")
    return ("\n".join(lines) + "\n").encode("utf-8")
