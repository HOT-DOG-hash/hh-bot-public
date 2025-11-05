# Progress Tracker (hh-bot-public)

| Block | Подзадача | Статус | Артефакты |
| --- | --- | --- | --- |
| P0.1 | Dev checks & smoke | ✅ ready | scripts/dev_check.sh; reports/release_preflight.md; reports/artifacts/README.md |
| P0.2 | Secrets & config | ✅ ready | env.example; docs/ops/secrets_checklist.md |
| P0.3 | Containers readiness | ✅ ready | Dockerfile; docker-compose.yml; docs/ops/container_readiness.md |
| P1.1 | API контракты (P1.1.3) | ✅ done (code-level sync) | docs/openapi/auto_campaigns.yaml; .spectral.yaml; docs/openapi/CHANGELOG.md |
| P1.2 | Observability & alerts | ✅ done (doc-level) | docs/ops/observability_spec.md; ops/alerts/p1.rules.example.yaml; checklist-progress/artifacts/P1.2/metrics_examples.txt |
| P1.3 | Dashboards & acceptance | ✅ done (doc-level) | docs/dashboards/REPORTING_SYNC.md; docs/dashboards/ACCEPTANCE.md; docs/dashboards/ACCESS_MODEL.md |
| P1.4 | Ranking decision docs | ✅ done (doc-level) | research/datasets/README.md; research/P2.1_RANKING_SPIKE.md; research/ml_ranking_report_TEMPLATE.md |
| P2.1 | Датасеты (P2.1.1) | ✅ done (doc-level) | research/P2.1_RANKING_SPIKE.md §2,§5; research/datasets/README.md; research/datasets/SAMPLE_SCHEMA.md |
| P2.1 | Offline-метрики (P2.1.2) | ✅ done (doc-level) | research/P2.1_RANKING_SPIKE.md §§6–7; research/offline_eval/README.md |
| P2.1 | Онлайн-метрики (P2.1.3) | ✅ done (doc-level) | research/P2.1_RANKING_SPIKE.md §9; backend/app/feature_flags.py; ops/experiments/AB_TEST_PLAN.md |
| P2.1 | Decision framework (P2.1.4) | ✅ done (doc-level) | research/P2.1_RANKING_SPIKE.md §10; research/ml_ranking_report_TEMPLATE.md |
| P2.2 | Партнёрские контракты (P2.2.1) | ✅ done (doc-level) | integration/P2.2_CONTRACTS.md; integration/ERRORS_STATUS_MATRIX.md |
| P2.2 | Пайплайн и схемы (P2.2.2) | ✅ done (doc-level) | integration/PIPELINE.md; integration/SCHEMAS.md |
| P2.2 | Моки и smoke (P2.2.3) | ✅ done (doc-level) | integration/mocks/README.md; integration/mocks/*.json; checklist-progress/artifacts/P2.2/smoke_scenarios.md |
| P2.2 | Monitoring & acceptance (P2.2.4) | ✅ done (doc-level) | integration/MONITORING.md; checklist-progress/artifacts/P2.2/metrics_examples.txt; docs/dashboards/ACCEPTANCE.md |
