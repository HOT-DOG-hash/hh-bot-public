# Partner Integrations — Monitoring Metrics

| Metric | TYPE | Labels | HELP / Purpose |
| --- | --- | --- | --- |
| `partner_ingest_total` | counter | `partner`, `endpoint` | Количество запросов к партнёру (успешных и неуспешных) |
| `partner_ingest_errors_total` | counter | `partner`, `endpoint`, `code` | Ошибки во время ingest (HTTP код или internal) |
| `partner_latency_seconds` | histogram | `partner`, `endpoint` | Латентность запросов к внешним API |
| `partner_quota_remaining` | gauge | `partner`, `window` | Остаток квоты (если партнёр возвращает header) |
| `partner_dedup_total` | counter | `partner`, `reason` | Количество удалённых дубликатов |
| `partner_payload_size_bytes` | histogram | `partner`, `endpoint` | Размер полезной нагрузки |

## Примеры строк
```
# HELP partner_ingest_total Total partner requests
# TYPE partner_ingest_total counter
partner_ingest_total{partner="hh",endpoint="/vacancies"} 128

# HELP partner_ingest_errors_total Total partner errors by code
# TYPE partner_ingest_errors_total counter
partner_ingest_errors_total{partner="hh",endpoint="/vacancies",code="429"} 3

# HELP partner_latency_seconds Partner API latency
# TYPE partner_latency_seconds histogram
partner_latency_seconds_bucket{partner="habr",endpoint="/jobs",le="0.5"} 12
partner_latency_seconds_bucket{partner="habr",endpoint="/jobs",le="1"} 30
partner_latency_seconds_sum{partner="habr",endpoint="/jobs"} 42.5
partner_latency_seconds_count{partner="habr",endpoint="/jobs"} 35
```

Примеры полностью собраны в `checklist-progress/artifacts/P2.2/metrics_examples.txt`.

## Alerts
- `partner_ingest_errors_total{code="429"}` рост >5% → алерт (привязан к Ops).
- `partner_latency_seconds` p95 > 3s → тикет.
- `partner_quota_remaining` < 5 → предупреждение.

## TODO
- Генерация этих метрик в сервисе интеграций.
