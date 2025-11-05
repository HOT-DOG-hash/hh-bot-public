# Release Preflight — Smoke Checklist

> Команды не запускаем автоматически; список для ручного смока перед релизом.

## 1. Dev Checks
1. `bash scripts/dev_check.sh`
   - Ожидаем: lint/type/test пройдены или soft-варнинги (если тулзы отсутствуют).
   - Артефакты: логи в `reports/artifacts/dev_check.log` (собрать вручную), обновление RUN_LOG.

## 2. API Smoke
1. `uv run -- python -m pytest backend/tests -m smoke`
   - Проверить: create/GET/PATCH кампании, idempotency, readyz.
   - Артефакты: `reports/artifacts/api_smoke.log`.

## 3. Integrations Smoke
1. `uv run -- python integration/scripts/mock_ingest.py --provider hh`
2. `uv run -- python integration/scripts/mock_ingest.py --provider habr`
   - Ожидаем: ingest success, обработка 429/5xx, дедупликация.
   - Артефакты: `reports/artifacts/integration_smoke.log`.

## 4. Metrics & Dashboards
1. Проверить `/metrics` → убедиться, что `campaign_*`, `partner_*` присутствуют.
2. Grafana импорт панелей (`docs/dashboards/grafana/*.json`).
3. Сохранить скриншоты/экспорт в `reports/artifacts/dashboards/`.

## 5. Checklist Update
- Запустить `python3 -X utf8 -u checklist-progress/scripts/checklist_update.py` после смоков.
- Зафиксировать результаты в RUN_LOG (`release preflight`).
