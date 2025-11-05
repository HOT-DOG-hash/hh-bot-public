# Observability Specification — Auto Campaigns (P1)

Версия: 2025-11-04

Документ согласовывает требования по наблюдаемости для этапа P1 (блоки P1.1 и P1.2). Основан на CAMPAIGN_AUTOMATION_SPEC.md, P1.1_ACCEPTANCE_TESTS.md, P1.2_SPEC.md и фактическом экспорте метрик (`checklist-progress/artifacts/P1.2/metrics_examples.txt`).

## 1. Служебные эндпоинты

### 1.1 `/health` (liveness)
- **Цель**: подтвердить, что процесс жив и цикл событий не заблокирован.
- **Ответ 200**: `{ "status": "ok", "version": "<build>" }` — генерируется без обращения к внешним зависимостям.
- **Неуспех**: любые исключения внутри сервиса → 500 (ошибка процесса). Не добавляем дополнительные проверки зависимостей.
- **Интервалы опроса**: 15 секунд (kubelet / ingress).

### 1.2 `/readyz` (readiness)
- **Цель**: убедиться, что сервис готов обрабатывать продовый трафик.
- **Обязательные проверки (реализация в `backend/app/core/startup_checks.py`)**:
  - БД (PostgreSQL) — запрос `SELECT 1` подтверждает доступность и состояние миграций.
  - Redis / Idempotency storage — `PING`; при отсутствии конфигурации возвращается `{"redis": "skipped"}`.
- **Ответы**:
  - 200: `{ "status": "ready", "components": {"db": "ready", "redis": "ready|skipped", ...} }`.
  - 503: `{ "status": "degraded", ... }` с перечислением деградировавших компонентов.
- **Интервалы опроса**: 30 секунд (blackbox-проба `hh-bot-readyz`).

### 1.3 `/metrics`
- **Формат**: стандартный Prometheus plaintext.
- **Экспорт**: все бизнес-метрики с префиксами `campaign_*`, `delivery_*`, `payments_*`, `webhook_*`, а также runtime (`python_gc_*`).
- **Защита**: доступ из сервисной сети; без аутентификации.

## 2. Каталог метрик (обязательный минимум)

| Metric | TYPE | Лейблы | Семантика / комментарий | Пример |
| --- | --- | --- | --- | --- |
| `campaign_created_total` | counter | `mode` | Количество созданных автокампаний по режиму (strict/wide). | `campaign_created_total{mode="strict"} 1` |
| `campaign_state_transitions_total` | counter | `from_state`, `to_state` | Количество переходов состояний кампаний. | `campaign_state_transitions_total{from_state="draft",to_state="active"} 2` |
| `campaign_idempotency_conflicts_total` | counter | `endpoint` | Конфликты идемпотентности по endpoint. | `campaign_idempotency_conflicts_total{endpoint="/api/v1/auto/campaigns"} 1` |
| `campaign_auto_pauses_total` | counter | `reason` | Автоматические паузы (например, `error_streak`). | `campaign_auto_pauses_total{reason="error_streak"} 1` |
| `campaign_delivery_logs_total` | counter | `result` | Исходы доставок (`sent`, `skipped`, `failed`). | `campaign_delivery_logs_total{result="skipped"} 4` |
| `delivery_attempt_errors_total` | counter | `type` | Ошибки доставок (`http_timeout`, `network5xx`, …). | `delivery_attempt_errors_total{type="http_timeout"} 2` |
| `campaign_scheduler_lag_seconds` | gauge | `partition` | Лаг шедулера (ключ SLO-OP-FRESH). | `campaign_scheduler_lag_seconds{partition="default"} 12.5` |
| `campaign_active_total` | gauge | `mode` | Текущее количество активных кампаний. | `campaign_active_total{mode="strict"} 3` |
| `campaign_operation_latency_seconds` | histogram | `operation` | Латентность операций (`create`, `start`, `skip`). | `campaign_operation_latency_seconds_bucket{operation="start",le="0.1"} 6` |
| `applications_sent_total` | counter | `plan_code` | Количество отправленных откликов ботом. | `applications_sent_total{plan_code="WEEKLY"} 15` |
| `daily_quota_remaining` | gauge | `plan_code` | Остаток квоты по тарифу. | `daily_quota_remaining{plan_code="WEEKLY"} 8` |
| `payments_initiated_total` | counter | `plan_code` | Инициированные платежи. | `payments_initiated_total{plan_code="WEEKLY"} 10` |
| `payments_succeeded_total` | counter | `plan_code` | Успешные платежи. | `payments_succeeded_total{plan_code="WEEKLY"} 9` |
| `payments_failed_total` | counter | `plan_code`, `reason` | Неуспешные платежи. | `payments_failed_total{plan_code="WEEKLY",reason="failed"} 1` |
| `payments_revenue_minor_total` | counter | `plan_code` | Выручка (минорные единицы). | `payments_revenue_minor_total{plan_code="WEEKLY"} 135000` |
| `payments_refunds_minor_total` | counter | `plan_code` | Рефанды (минорные единицы). | `payments_refunds_minor_total{plan_code="WEEKLY"} 0` |
| `webhook_lag_seconds` | histogram | — | Лаг между событием провайдера и обработкой. | `webhook_lag_seconds_bucket{le="1"} 24` |

> Источник живых примеров: `checklist-progress/artifacts/P1.2/metrics_examples.txt`.

## 3. Минимальные SLO / SLA

| SLO ID | Scope | Target | Метрика / условие | Связанный алерт |
| --- | --- | --- | --- | --- |
| SLO-OP-AVAIL | Доступность `/readyz` | ≥ 99.0% за 7 дней | `avg_over_time(probe_success{job="hh-bot-readyz"}[5m])` | `AutoCampaignReadyFailure` |
| SLO-OP-FRESH | Актуальность шедулера | Lag ≤ 120 c | `campaign_scheduler_lag_seconds` | `BackoffStuck` |
| SLO-OP-QUALITY | Бурсты ошибок доставок | ≤ 5 ошибок / 5 мин | `increase(delivery_attempt_errors_total[5m])` | `AutoCampaignErrorBurst` |
| SLO-BILLING-SUCCESS | Конверсия платежей | Успех ≥ 92% / 10 мин | `increase(payments_succeeded_total[10m]) / clamp_min(increase(payments_initiated_total[10m]), 1)` | `PaymentsFailureRateHigh` |
| SLO-NOTIFY-LAT | Лаг вебхуков | p95 ≤ 60 c | `histogram_quantile(0.95, sum by (le) (rate(webhook_lag_seconds_bucket[15m])))` | `NotificationLatencyHigh` |
| SLO-RETENTION | Рост пропусков отправок | ≤ 1.5× baseline | `increase(campaign_delivery_logs_total{result="skipped"}[10m]) / clamp_min(increase(campaign_delivery_logs_total{result="sent"}[10m]), 1)` | `OptOutSpike` |

## 4. Alert Rules (каркас)

Ниже YAML-фрагменты для Prometheus rule files. Имя группы и выражения согласованы с ACCEPTANCE.md.

```yaml
# group: auto_campaigns (пример)
- alert: AutoCampaignErrorBurst
  expr: increase(delivery_attempt_errors_total[5m]) > 5
  for: 5m
  labels:
    severity: page
  annotations:
    summary: "Бурст ошибок доставки >5 за 5м"
    runbook: "ops/runbooks/autocampaigns/error_burst.md"

- alert: BackoffStuck
  expr: avg_over_time(campaign_scheduler_lag_seconds[5m]) > 120
  for: 10m
  labels:
    severity: ticket
  annotations:
    summary: "Лаг шедулера превышает 120с"
    runbook: "ops/runbooks/autocampaigns/scheduler_lag.md"

- alert: AutoCampaignReadyFailure
  expr: avg_over_time(probe_success{job="hh-bot-readyz"}[5m]) < 1
  for: 5m
  labels:
    severity: page
  annotations:
    summary: "readiness-проба /readyz возвращает ошибки"
    runbook: "ops/runbooks/autocampaigns/ready_failure.md"

- alert: NotificationLatencyHigh
  expr: histogram_quantile(0.95, sum by (le) (rate(webhook_lag_seconds_bucket[15m]))) > 60
  for: 15m
  labels:
    severity: ticket
  annotations:
    summary: "p95 латентности вебхуков > 60с"
    runbook: "ops/runbooks/autocampaigns/notification_latency.md"

- alert: OptOutSpike
  expr: (increase(campaign_delivery_logs_total{result="skipped"}[10m]) / clamp_min(increase(campaign_delivery_logs_total{result="sent"}[10m]), 1)) > 1.5
  for: 10m
  labels:
    severity: info
  annotations:
    summary: "Доля пропущенных отправок > 150% от отправленных за 10 минут"
    runbook: "ops/runbooks/autocampaigns/optout_spike.md"

- alert: PaymentsFailureRateHigh
  expr: (increase(payments_failed_total[10m]) / clamp_min(increase(payments_initiated_total[10m]), 1)) > 0.08
  for: 10m
  labels:
    severity: ticket
  annotations:
    summary: "Доля неуспешных платежей превысила 8% за 10 минут"
    runbook: "ops/runbooks/billing/payments_failure.md"
```

> Финальные значения выражений и порогов должны быть подтверждены при внедрении; текущий документ фиксирует согласованный skeleton.
