# Partner Integrations — Error Handling Matrix

| HTTP Code / Provider | Error Code | Description | Retry Policy | Client Action | Alert Level |
| --- | --- | --- | --- | --- | --- |
| 400 (hh.ru) | `VALIDATION` | Некорректные поля | No retry | Log & notify partner, move payload to `validation_errors` | info |
| 401 (hh.ru) | `AUTH_FAILED` | Токен просрочен | Acquire new token, retry once | Refresh OAuth credentials | ticket |
| 409 (hh.ru) | `IDEMPOTENT_REPLAY` | Idempotency mismatch | No retry | Compare payload hash, escalate to partner | ticket |
| 429 (hh.ru) | `RATE_LIMIT` | Превышен лимит | Backoff 10s/30s/60s | Respect `Retry-After`, emit `partner_ingest_errors_total{code="rate_limit"}` | info |
| 500 (hh.ru) | `UPSTREAM_ERROR` | Внутренняя ошибка | Backoff 5s/15s, max 3 attempts | Log correlation_id, push to DLQ после неудач | warning |
| 400 (Habr) | `VALIDATION` | Некорректные поля | No retry | Отправить отчёт партнёру, пометить запись как failed | info |
| 401 (Habr) | `AUTH_FAILED` | API ключ невалиден | No retry | Rotate API key, повторить вручную | ticket |
| 409 (Habr) | `IDEMPOTENT_REPLAY` | Digest конфликтует | No retry | Проверить `X-Request-Digest`, дослать ack | info |
| 429 (Habr) | `RATE_LIMIT` | Превышен лимит | Backoff 5s/15s/45s | Использовать `Retry-After` | info |
| 503 (Habr) | `SERVER_ERROR` | Проблемы сервиса | Backoff 10s/30s | Записать в DLQ, алерт при >3 подряд | warning |
| 400 (Generic) | `VALIDATION` | Общая валидация | No retry | Обновить маппинг, уведомить провайдера | info |
| 401 (Generic) | `AUTH_FAILED` | HMAC подпись неверна | No retry | Проверить секрет/время запроса | ticket |
| 429 (Generic) | `RATE_LIMIT` | Лимит | Backoff 15s/30s/60s | Reschedule job | info |
| 500 (Generic) | `SERVER_ERROR` | Внутренняя ошибка | Backoff 5s/15s/45s | После 3 неудач — алерт | warning |
| 504 (Generic) | `TIMEOUT` | Таймаут сети | Retry 5s/15s/45s | Проверить связность, DLQ | ticket |

- Все ошибки логируются с `X-Request-Id`.
- Повторяющиеся ошибки >5/5m → alert `PartnerIngestErrorSpike`.
- Клиентское поведение реализуется в ingest worker согласно `integration/PIPELINE.md`.
