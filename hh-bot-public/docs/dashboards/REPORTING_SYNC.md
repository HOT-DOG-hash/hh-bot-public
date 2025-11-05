# Dashboard Reporting Sync — Auto Campaigns (P1)

Документ связывает метрики Prometheus с панелями Grafana и источниками данных.
Требования сверены со спецификацией `docs/dashboards/P1.2_SPEC.md`, доступной моделью
`docs/dashboards/ACCESS_MODEL.md` и JSON экспортами в `docs/dashboards/grafana/`.

| Metric | Panel / Query | Dashboard | Data Source | Notes |
| --- | --- | --- | --- | --- |
| `campaign_state_transitions_total` | panel **“Active Campaign Delta”** (`sum(increase(...{to_state="active"})) - sum(increase(...{to_state=~"paused\|archived"}))`) | Operational (`Auto Campaigns - Operational`) | Prometheus (`DS_PROMETHEUS`) | Tracks net change of active campaigns, aligns with KPI “Active auto-campaigns”. |
| `campaign_auto_pauses_total` | panel **“Auto Pauses by Reason”** (`sum by (reason) increase(...)`) | Operational | Prometheus | Mirrors auto-pause reasons, feeds runbook `pause_campaign`. |
| `campaign_scheduler_lag_seconds` | panel **“Scheduler Lag (5m avg)”** (`avg_over_time(...[5m])`) | Operational | Prometheus | SLO-OP-FRESH signal; partition filter bound to `$service`. |
| `delivery_attempt_errors_total` | panel **“Delivery Errors by Type”** (`sum by (type) increase(...)`) | Operational | Prometheus | Error taxonomy for delivery worker guard-rails. |
| `payments_initiated_total`, `payments_succeeded_total` | panel **“Plan Conversion (7d)”** (ratio of 7d increases) | Growth & Billing (`Growth & Billing`) | Prometheus | Implements conversion KPI per plan (`$plan` variable). |
| `payments_revenue_minor_total`, `payments_refunds_minor_total` | panel **“Revenue vs Refunds”** (`increase(...) / 100`) | Growth & Billing | Prometheus | Converts minor units → currency; plotted as dual time series. |
| `payments_failed_total` | panel **“Failed Payments by Reason”** (`sum by (plan_code, reason) increase(...)`) | Growth & Billing | Prometheus | Differentiates provider vs customer failures; supports finance RBAC. |
| `webhook_lag_seconds` | panel **“Webhook Lag p95”** (`histogram_quantile` over `webhook_lag_seconds_bucket`) | Growth & Billing | Prometheus | Tracks partner latency; referenced by SLO-NOTIFY-LAT. |

## Variable & RBAC Alignment

- `$env`, `$service`, `$plan` declared in both dashboards; visibility and defaults conform to
  `ACCESS_MODEL.md` (Finance locked to `$env="prod"`, `$service` hidden read-only).
- Datasource UID is parameterized (`DS_PROMETHEUS`); import instructions in Grafana README remain valid.
