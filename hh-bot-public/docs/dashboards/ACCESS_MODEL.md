# Auto Campaign Dashboards — Access Model & Data Handling

## 1. RBAC & Dashboards
| Role | Audience | Scope | Permissions | Dashboards |
| --- | --- | --- | --- | --- |
| `auto_campaigns.monitor` | DevOps, Backend on-call | Prod Prometheus / Grafana | View operational dashboard, acknowledge alerts, inspect `$env`/`$service` filters | Operational |
| `auto_campaigns.analytics` | Product, Growth analysts | Prod Grafana + S3 exports | View both dashboards, export CSV/JSON with hashed identifiers, schedule report snapshots | Operational, Growth & Payments |
| `finance.read` | Finance & Billing | Growth data only | View Growth & Payments dashboard, download revenue aggregates (no campaign drill-down) | Growth & Payments |
| `auto_campaigns.admin` | Platform owners | Full | Manage RBAC, edit dashboards/alerts, approve sharing workflow, purge exports | All |

- All roles are provisioned via corporate SSO (MFA enforced). Elevation beyond role defaults requires ticket approval and is logged as `dashboard.access.grant` in the audit trail.

## 2. Dashboard Variables & Scope
| Variable | Source | Description | Visibility Guard |
| --- | --- | --- | --- |
| `$env` | Prometheus label `env` | Target environment (`prod`, `staging`, `dev`) | `finance.read` pinned to `prod`; others default to `All`. |
| `$service` | Prometheus label `partition` | Scheduler / worker shard | Hidden for Finance; shown read-only for analytics. |
| `$plan` | Prometheus label `plan_code` | Billing plan (`WEEKLY`, `MONTHLY`) | Available to all; exports aggregate by plan only. |

- Operational dashboard is shared with `auto_campaigns.monitor` first, then with `auto_campaigns.analytics` after validation.
- Growth & Payments dashboard is shared sequentially: analytics → finance → product leadership, after masking checks are confirmed.

## 3. Data Classification & PII Handling
| Dataset | PII | Controls | Retention / TTL |
| --- | --- | --- | --- |
| DS-01 (campaign tables) | Telegram/user IDs | Hash identifiers (SHA-256 + salt) before export; truncate rendered IDs to last 4 chars | Raw DB 180 d · dashboard exports 14 d |
| DS-02 (Prometheus metrics) | None | Labels exclude direct PII; campaign_id is UUID | Prometheus TSDB 30 d |
| DS-03 (payments) | User/account IDs, revenue | Hash user IDs, aggregate to day-level totals, no individual receipts | Warehouse 365 d · dashboard export 30 d |
| DS-04 (CRM events) | Email, telecom | Replace with surrogate keys; opt-out reason kept | 180 d |
| DS-05 (webhook logs) | External partner IDs | Show provider + latency only; stash payload in secure bucket | 90 d |
| DS-07 (partner telemetry) | None | No extra controls | 90 d |

## 4. Export & Snapshot Lifecycle
- CSV/JSON exports allowed for `auto_campaigns.analytics` and `finance.read`; each export records `actor_id`, `dashboard_id`, row count, and scheduled deletion timestamp.
- Default export TTL: 14 days (analytics) / 30 days (finance). Files reside in encrypted S3 bucket `auto-campaigns-dashboards` with server-side KMS.
- Grafana PDF/PNG snapshots stored in `checklist-progress/artifacts/P1.2/` (prefixed by dashboard UID) and pruned after 30 days via scheduled job.
- Browser caching is disabled (`Cache-Control: no-store`) for routes exposing metrics with quasi-PII.

## 5. Sharing & Compliance Workflow
1. Admin provisions role bindings and validates dashboard variables for the target audience.
2. Operational dashboard shared with `auto_campaigns.monitor`; after one week of green alerts the link is shared with analytics.
3. Growth & Payments dashboard shared only after PII masking checks pass (recorded as `dashboard.sharing.approved`).
4. Quarterly access review led by Platform → report stored in Confluence and mirrored to `campaign_audit_log`.
5. Any RBAC or alert change must go through pull-request review; deployment artifacts archived for ≥12 months.
