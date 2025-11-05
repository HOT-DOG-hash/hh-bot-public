# Partner Data Pipeline (P2.2.2)

## 1. Overview
Интеграционный пайплайн состоит из четырёх этапов: ingest → normalize → validate → store.

### 1.1 Ingest
- **Триггер**: cron job (`integration/schedules.yaml`) + on-demand вызов для realtime webhooks.
- **Провайдеры**:
  - hh.ru — OAuth 2.0 client credentials, батчи `per_page=100`, pull каждые 15 минут.
  - Habr Career — API key + cursor, батчи по 1 000 записей, pull каждые 30 минут.
  - Generic — webhook + fallback polling (1 час).
- **Идемпотентность**:
  - Ключ `ingest_key = sha256(partner_code || external_id || updated_at_iso)`.
  - Запись в `partner_ingest_log` (см. SCHEMAS) с `hash_payload`.
  - Повторный payload с тем же hash → пропускаем, но обновляем `ingested_at`.
- **Ошибки**:
  - 429/5xx обрабатываются по стратегиям `P2.2_CONTRACTS.md` с backoff и DLQ (`var/dlq/partner_<code>.jsonl`).
  - Невалидные ответы сохраняем в `integration/logs/errors/`.

### 1.2 Normalize
- **Mapping**:
  - Поля приводятся к внутренним именам (`title`, `description_raw`, `salary_minor`, `currency`, `location_country`, ...).
  - Конвертация валют — сервис `fx.get_rate(at=payload.updated_at)`.
  - Нормализация локаций — reference таблицы `geo_countries`, `geo_regions`, `geo_cities` (ISO-3166).
- **PII**:
  - В описаниях контакты вырезаются (regex + NER), сохраняется поле `has_contacts` (bool).
  - Компания нормализуется через `partner_companies` (по `external_company_id`).
- **Outputs**:
  - Нормализованный batch в Parquet (`tmp/normalize/<partner>/<ts>.parquet`).
  - Статистика (кол-во полей, пропуски) в `integration/logs/normalize_stats_<ts>.json`.

### 1.3 Validate
- **Обязательные поля**: `title`, `description`, `company`, `salary_minor`, `currency`, `location_country`.
- **Дедупликация**:
  - Жёсткий ключ: `(partner_code, external_id)` (дубликаты → update).
  - Мягкий ключ: `(normalized_company, title_hash, location_city)` — при совпадении записываем в `partner_dedup_events`.
- **Правила**:
  - Зарплата: `0 < salary_minor ≤ 50_000_000`.
  - Валюта: входит в разрешённый список `["RUB","USD","EUR","KZT"]`.
  - Локация: ISO country code, city из справочника. Несоответствия → `validation_status=FAILED`.
- **Результаты**:
  - Успешные — в staging (см. Store).
  - Ошибки — в `integration/logs/validation_<ts>.json` с `reason`, `field`, `value`.

### 1.4 Store
- **Staging**: загружаем Parquet batch через COPY/`COPY ... FROM STDIN` в таблицу `partner_vacancies_staging`.
- **Core**:
  - merge (`INSERT ... ON CONFLICT`) в `partner_companies`, затем `partner_vacancies`.
  - Статус вакансий обновляется через `status = CASE WHEN payload.closed THEN 'inactive' ELSE 'active'`.
- **Audit**:
  - Каждое изменение записывается в `partner_ingest_log` (payload hash), плюс CDC событие в Kafka topic `partner.vacancy.cdc`.
- **Retention**:
  - Staging чистится каждые 14 дней (`DELETE WHERE ingested_at < now()-14d`).
  - Core хранит историю статусов (вспомогательная таблица `partner_vacancy_history`).

## 2. Formats
- Intermediates: Parquet (gzip) для батчей, JSON для realtime webhook.
- Encoding: UTF-8; временные метки — UTC ISO8601.

## 3. Monitoring
- Метрики (`integration/MONITORING.md`):
  - `partner_ingest_total{partner,stage}` — количество записей на этап.
  - `partner_ingest_errors_total{partner,stage,code}` — ошибки ingest/normalize/validate.
  - `partner_dedup_total{partner,type}` — soft/hard дедуп.
  - `partner_pipeline_duration_seconds_bucket{stage}` — время прохождения этапов.
- Логи: структурированные JSON (логгер `integration.pipeline`), уровень `INFO/ERROR`.
- Алерты: отсутствие ingest > 1 часа (`partner_ingest_total`), рост ошибок >5%/5 минут, лаг вебхуков (`partner_webhook_lag_seconds`).

## 4. Execution Plan
1. Реализовать коннектор hh.ru (pull) и Habr (cursor) → выкладка ingest сервисов.
2. Настроить Redis кэш idempotency (алгоритм sliding window).
3. Подготовить нормализационные словари (валюты, локации, employment types).
4. Включить CI пайплайн: `pytest integration/tests/`, `ruff` формат, `mypy`.
5. Согласовать расписания cron и лимиты с SRE (см. `docs/ops/observability_spec.md`).
