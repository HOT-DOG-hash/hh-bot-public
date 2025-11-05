# Release Artifacts

Собирать перед деплоем и складывать в этот каталог (или подпапки):

- `dev_check.log` — вывод `scripts/dev_check.sh`.
- `api_smoke.log` — результаты smoke-тестов API.
- `integration_smoke.log` — ingest/normalize smoke.
- `dashboards/` — экспорт панелей Grafana (PNG/JSON) и метрик `/metrics` сниппеты.
- `offline_metrics/metrics_summary.csv` — итоговые оффлайн метрики.
- `ml_ranking_report.md` — заполненный шаблон отчёта.

Все файлы должны иметь дату в имени (например, `dev_check_2025-11-04.log`).
