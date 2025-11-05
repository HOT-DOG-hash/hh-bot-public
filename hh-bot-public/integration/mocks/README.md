# Partner API Mocks

Каталог `integration/mocks/` содержит набор статичных ответов провайдеров,
используемых для локального тестирования ingest пайплайна и smoke-сценариев.
Моки синхронизированы с контрактами (`integration/P2.2_CONTRACTS.md`) и матрицей
ошибок (`integration/ERRORS_STATUS_MATRIX.md`).

```
integration/mocks/
├─ hh_vacancies_page.json          # Happy path (hh.ru)
├─ hh_rate_limit.json              # 429 + Retry-After (hh.ru)
├─ hh_server_error.json            # 500 upstream error
├─ habr_export_batch.json          # Happy path (Habr Career cursor)
├─ habr_missing_fields.json        # Пустые/некорректные поля
├─ generic_broken_encoding.json    # Неверная кодировка payload
└─ README.md
```

## Файлы и сценарии

| File | Scenario | Details |
| --- | --- | --- |
| `hh_vacancies_page.json` | Happy path | Страница из `/vacancies` hh.ru, включает полно заполненные поля, `updated_at`. |
| `hh_rate_limit.json` | 429 retry | Модель ответа при превышении лимита с заголовками `X-RateLimit-*`, `Retry-After`. |
| `hh_server_error.json` | 5xx retry | Типичный 500 с `correlation_id`, проверка backoff → DLQ. |
| `habr_export_batch.json` | Happy path (cursor) | Batch из `/vacancies/export` Habr Career, содержит `next_cursor`. |
| `habr_missing_fields.json` | Пустые поля | Отклоняемые записи (отсутствует salary/location, пустой `description`). |
| `generic_broken_encoding.json` | Broken encoding | Payload с base64, иллюстрирующий некорректный UTF-8 (используется для negative tests). |

## Обновление моков
1. При изменении контрактов или схем обновить соответствующие JSON.
2. Добавить комментарий в `checklist-progress/RUN_LOG.md` (формат `P2.2 mocks update`).
3. Версионировать файлы по датам при необходимости (`hh_vacancies_page-20251104.json`).
4. Прогнать smoke-сценарии (`checklist-progress/artifacts/P2.2/smoke_scenarios.md`)
   перед merge; при успехе обновить артефакт.

## Использование
- Интеграционные/юнит тесты ingest: подмена HTTP ответов.
- Демонстрация обработчиков ошибок (rate-limit, backoff, idempotency).
- CI smoke: curl/pytest прогон с проверкой кодов статуса и содержимого.
