# Auto Campaign Dashboards — Acceptance & Alerting Requirements

## 1. Service Level Objectives
| SLO ID | Scope | Target | Measurement | Linked Alert |
| --- | --- | --- | --- | --- |
| SLO-OP-AVAIL | Operational dashboard availability | ≥ 99.0 % за 7 дней | Synthetic GET `/d/auto-operational` success rate | `AutoCampaignReadyFailure` |
| SLO-OP-FRESH | Operational data freshness | Prometheus scrape age ≤ 120 с | `now - max(scrape_timestamp(campaign_scheduler_lag_seconds, delivery_attempt_errors_total))` | `BackoffStuck` |
| SLO-OP-QUALITY | Delivery health | Error bursts ≤ 5 за 5 мин | `increase(delivery_attempt_errors_total[5m])` | `AutoCampaignErrorBurst` |
| SLO-GR-AVAIL | Growth & Billing dashboard availability | ≥ 97.5 % за 7 дней | Grafana availability log | `DashboardAvailabilityDegraded` |
| SLO-GR-FRESH | Billing data freshness | Warehouse lag ≤ 90 мин | `now - dwh_last_refresh` | `PaymentsDataStale` |
| SLO-NOTIFY-LAT | Notification/webhook latency | p95 ≤ 60 с | `histogram_quantile(0.95, rate(delivery_notification_latency_seconds_bucket[15m]))` | `NotificationLatencyHigh` |
| SLO-RETENTION | Opt-out / retention guardrail | `applications_skipped_total{reason="user_skip"}` ≤ 1.5× baseline | 3h rolling ratio to previous week | `OptOutSpike` |

- SLO targets are reviewed quarterly; deviations require documented RCA and follow-up tasks.
- Freshness calculations rely on runbook scripts stored in `ops/runbooks/auto_campaigns/`.

## 2. Alert Catalogue Mapped to `ops/alerts/alerts.yml`
| Alert | Expression | Threshold & Window | Severity | Escalation | Notes |
| --- | --- | --- | --- | --- | --- |
| AutoCampaignErrorBurst | `increase(delivery_attempt_errors_total[5m]) > 5` | 5 мин burst > 5 ошибок | page | DevOps on-call | Mirrors SLO-OP-QUALITY. |
| BackoffStuck | `avg_over_time(campaign_scheduler_lag_seconds[5m]) > 120` | 5 мин среднее > 120 с, `for: 10m` | ticket | Backend + SRE | Signals scheduler stale queue. |
| AutoCampaignReadyFailure | `min_over_time(campaign_ready_state[5m]) < 1` | Компонент = 0 ≥ 5 мин | page | DevOps on-call | Component label used for paging. |
| NotificationLatencyHigh | `histogram_quantile(0.95, sum by (channel, le) (rate(delivery_notification_latency_seconds_bucket[15m]))) > 60` | p95 > 60 с 15 мин | ticket | Backend | Channel-specific annotations in rule. |
| OptOutSpike | `rate(applications_skipped_total{reason="user_skip"}[10m]) > 0.05` | > 5 %/мин в течение 10 мин | info | Product analytics | Relates to retention guardrail. |
| DashboardAvailabilityDegraded | `probe_success{job="grafana-health"} < 0.9` | error rate > 10 % за 5 мин | page | DevOps on-call | Synthetic check configured in Blackbox exporter. |
| PaymentsDataStale | `dwh_last_refresh_age_minutes > 90` | одно срабатывание | ticket | Billing analytics | Already present в `payments` группе. |
| HighPaymentFailRate | `rate(payments_failed_total[10m]) / ... > 0.08` | как в yaml | page | Billing on-call | Keeps existing payments alert. |
| WebhookLagTooHigh | `histogram_quantile(0.95, rate(webhook_lag_seconds_bucket[15m])) > 900` | p95 > 15 мин | ticket | Integrations | Aligned with webhook SLA. |

- Alert runbooks referenced in annotations (e.g. `runbook: ops/runbooks/autocampaigns/error_burst.md`), maintained alongside rules.
- Prometheus rule updates require `promtool check rules ops/alerts/alerts.yml` prior to merge; artefact stored in `artifacts/P0.5/promtool_check.txt`.

## 3. Acceptance Checklist
1. **Import validation**
   - Upload `docs/dashboards/grafana/operational.json` → Prometheus datasource bound → panel queries return non-empty series.
   - Upload `docs/dashboards/grafana/growth_billing.json` → verify plan conversion and revenue panels render data (use `$plan=WEEKLY` smoke).
2. **Variable sanity**
   - `$env`, `$service`, `$plan` variables resolve values; Finance role pinned to `$env=prod`.
3. **Alert linkage**
   - All SLOs mapped to active alerts in `ops/alerts/alerts.yml`; promtool check succeeds.
   - Alertmanager routes escalate according to severity table; paging destinations confirmed.
4. **Export logging**
   - Export action writes audit record (`dashboard.export`) with TTL metadata.
5. **Documentation**
   - ACCESS_MODEL.md and this file stored in repo, linked from runbook.
   - `checklist-progress/artifacts/P1.2/dashboards_checklist.md` updated with import smoke results.

Acceptance is complete when the checklist items are satisfied for both dashboards and all alerts have passed promtool validation.

## 4. Auto Campaigns RBAC & Acceptance Flow

| Step | Expected Result | Evidence / Owner |
| --- | --- | --- |
| Provision `auto_campaigns.monitor` role | Role can view Operational dashboard, filter by `$env/$service`, cannot edit panels | Access review export (`dashboard.access.grant`) · Ops owner |
| Provision `auto_campaigns.analytics` role | Role can view both dashboards, export CSV with hashed identifiers, `$service` read-only | Grafana sharing log · Product analytics |
| Provision `finance.read` role | Role restricted to Growth & Billing dashboard, `$env` pinned to `prod`, exports truncated to plan-level aggregates | Export audit trail (`dashboard.export`) · Finance tech |
| Validate admin rollback (`auto_campaigns.admin`) | Admin can revoke/share roles, update alert contact points | Change record in RBAC runbook |

- RBAC tests executed after each dashboard import; outcomes appended to
  `checklist-progress/artifacts/P1.2/dashboards_checklist.md`.
- Any deviation requires remediation entry in `checklist-progress/RUN_LOG.md` and update to
  `docs/dashboards/ACCESS_MODEL.md`.
