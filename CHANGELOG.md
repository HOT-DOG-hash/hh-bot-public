# Changelog — hh-bot MVP 3.0 (Doc Freeze 2025-11-04)

## P0 — Platform Readiness
- Dev checks & smoke script (`scripts/dev_check.sh`, reports/release_preflight.md).
- Secrets audit & container readiness docs (`docs/ops/secrets_checklist.md`, `docs/ops/container_readiness.md`).
- Ops hardening: readyz health, alerts, nginx security, metrics snapshots.

## P1 — Auto Campaigns
- Product spec, data model, and OpenAPI 3.1 contract (`design/CAMPAIGN_AUTOMATION_SPEC.md`, `docs/openapi/auto_campaigns.yaml`).
- Observability & dashboards (docs/dashboards/*.json, docs/dashboards/ACCEPTANCE.md, ops/alerts).
- Ranking spike documentation: datasets, offline/online metrics, decision framework.

## P2 — Partner Integrations
- API contracts, error matrix, ingest pipeline & schemas (`integration/P2.2_CONTRACTS.md`, `integration/PIPELINE.md`, `integration/SCHEMAS.md`, `integration/ERRORS_STATUS_MATRIX.md`).
- Mocks & smoke scenarios (`integration/mocks/`, checklist-progress/artifacts/P2.2/smoke_scenarios.md).
- Monitoring contract & acceptance (`integration/MONITORING.md`, docs/dashboards/ACCEPTANCE.md).
