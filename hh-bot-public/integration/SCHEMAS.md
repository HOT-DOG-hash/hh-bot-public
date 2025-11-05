# Storage Schemas — Partner Integrations (P2.2.2)

Документ описывает таблицы staging/core и вспомогательные структуры, необходимые
для ingest пайплайна (см. `integration/PIPELINE.md`). Все поля в UTC, encoding UTF-8.

## 1. Staging Layer (`schema = partner_staging`)
| Column | Type | Notes |
| --- | --- | --- |
| `partner_code` | text | (`hhru`, `habr`, `generic_x`). |
| `external_id` | text | Идентификатор вакансии у партнёра. |
| `title` | text | Обрезается до 512 символов. |
| `description` | text | Сырый HTML/Markdown. |
| `salary_minor` | bigint | Значение в минимальных единицах (RUB kopecks). |
| `currency` | char(3) | ISO 4217. |
| `salary_currency_rate` | numeric(12,6) | Курс конвертации в момент ingest. |
| `location_country` | char(2) | ISO 3166-1 alpha-2. |
| `location_region` | text | Нормализованное название. |
| `location_city` | text | Нормализованное название. |
| `geo_lat`, `geo_lon` | numeric(9,6) | Необязательные координаты. |
| `company_name` | text | До нормализации. |
| `company_external_id` | text | Если предоставляется. |
| `employment_type` | text | `full_time`, `part_time`, `contract`, `remote`. |
| `experience_level` | text | Junior/Middle/Senior/Lead. |
| `skills` | jsonb | Массив строк. |
| `raw_payload` | jsonb | Оригинал ответа. |
| `ingested_at` | timestamptz | Время ingest. |
| `updated_at_partner` | timestamptz | `updated_at` из payload. |
| `ingest_key` | uuid | SHA256→UUID хэш из `(partner_code, external_id, updated_at_partner)`. |
| `hash_payload` | char(64) | SHA256 payload. |
| `validation_status` | text | `pending`, `passed`, `failed`. |
| `validation_errors` | jsonb | Детали ошибок. |

- **Primary key**: `(partner_code, external_id, updated_at_partner)`.
- **Unique constraint**: `(partner_code, external_id, hash_payload)`.
- **Indexes**:
  - `idx_staging_ingested_at` (`ingested_at desc`) — для TTL.
  - `idx_staging_validation_status` — для повторной проверки.
- **Retention**: 14 дней (cron `DELETE`).

## 2. Core Layer (`schema = partner_core`)

### 2.1 `partner_companies`
| Column | Type | Notes |
| --- | --- | --- |
| `company_id` | bigserial | surrogate PK. |
| `partner_code` | text | |
| `external_company_id` | text | nullable. |
| `normalized_name` | citext | lower-case. |
| `normalized_location` | citext | country/city. |
| `contacts_masked` | boolean | флаг наличия контактов (true если были и замаскированы). |
| `created_at` | timestamptz | default now(). |
| `updated_at` | timestamptz | |

- **Constraints**:
  - PK `partner_companies_pkey` (`company_id`).
  - Unique `uq_companies_partner_external` (`partner_code`, `external_company_id`).
  - Index `idx_companies_name` (`normalized_name`).

### 2.2 `partner_vacancies`
| Column | Type | Notes |
| --- | --- | --- |
| `vacancy_id` | bigserial | PK. |
| `company_id` | bigint | FK → `partner_companies.company_id`. |
| `title` | text | |
| `title_hash` | char(64) | SHA256 нормализованного заголовка. |
| `description` | text | Уже очищенный текст. |
| `description_vector` | vector(768) | Опционально — эмбеддинг. |
| `salary_minor` | bigint | |
| `currency` | char(3) | |
| `salary_currency_rate` | numeric(12,6) | |
| `location_country` | char(2) | |
| `location_region` | text | |
| `location_city` | text | |
| `geo_lat`, `geo_lon` | numeric(9,6) | |
| `employment_type` | text | |
| `experience_level` | text | |
| `skills` | jsonb | |
| `source_partner` | text | |
| `source_external_id` | text | |
| `source_ingest_key` | uuid | |
| `status` | text | `active`, `inactive`, `archived`. |
| `status_changed_at` | timestamptz | |
| `first_seen_at` | timestamptz | |
| `updated_at` | timestamptz | |

- **Constraints**:
  - Unique `uq_vacancies_partner_external` (`source_partner`, `source_external_id`).
  - Index `idx_vacancies_company` (`company_id`).
  - Index `idx_vacancies_status` (`status`, `updated_at desc`).
  - GIN index `idx_vacancies_skills` ON `skills`.
  - Partial index `idx_vacancies_active_city` ON `(location_city)` WHERE `status='active'`.

### 2.3 `partner_vacancy_history`
| Column | Type | Notes |
| --- | --- | --- |
| `history_id` | bigserial | PK. |
| `vacancy_id` | bigint | FK → `partner_vacancies`. |
| `change_type` | text | `created`, `updated`, `closed`. |
| `payload_before` | jsonb | nullable. |
| `payload_after` | jsonb | nullable. |
| `changed_at` | timestamptz | |
| `changed_by` | text | `pipeline`, `manual`. |

- Index `idx_history_vacancy` (`vacancy_id`, `changed_at desc`).

## 3. Audit & Idempotency Tables

### 3.1 `partner_ingest_log`
| Column | Type | Notes |
| --- | --- | --- |
| `log_id` | bigserial | PK. |
| `partner_code` | text | |
| `external_id` | text | |
| `ingest_key` | uuid | |
| `hash_payload` | char(64) | |
| `ingested_at` | timestamptz | |
| `status` | text | `processed`, `duplicate`, `failed`. |
| `error_reason` | text | nullable. |

- Unique `uq_ingest_log_partner_key` (`partner_code`, `ingest_key`).
- Index `idx_ingest_log_status` (`status`).
- Retention 90 дней (для расследований).

### 3.2 `partner_dedup_events`
| Column | Type | Notes |
| --- | --- | --- |
| `event_id` | bigserial | PK. |
| `partner_code` | text | |
| `primary_vacancy_id` | bigint | FK → `partner_vacancies`. |
| `duplicate_vacancy_id` | bigint | FK → `partner_vacancies`. |
| `dedup_rule` | text | `hard_key`/`soft_company_title_location`. |
| `created_at` | timestamptz | |
| `resolved_at` | timestamptz | nullable. |

- Index `idx_dedup_partner` (`partner_code`, `created_at desc`).
- Используется аналитиками для мониторинга кол-ва дублей.

## 4. Warehousing & Downstream
- Репликация в ClickHouse через Debezium topics (`partner.vacancies`, `partner.companies`).
- Материализованные виды:
  - `mv_partner_vacancies_active` — только активные, обновляется раз в 15 минут.
  - `mv_partner_company_stats` — агрегаты по компаниям/партнёрам.
- BI слой: таблица `bi_partner_metrics` (daily snapshot), источники — `partner_vacancies`, `partner_vacancy_history`.

## 5. Maintenance & Retention
- Staging TTL 14 дней, history 365 дней.
- Индексы пересчитываются еженедельно (`REINDEX CONCURRENTLY`) для JSON/GIN.
- VACUUM `partner_vacancies` nightly; autovacuum thresholds подняты (`scale_factor 0.1`).
- Schema migrations оформляются Alembic ревизиями `integration/versions/*.py`.
