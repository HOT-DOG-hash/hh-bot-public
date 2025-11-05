# PAYMENT_SCHEMA_SPEC

> Состояние: 2025-10-24 (ветка `chore/mvp3-refactor`)

## Общие принципы
- Все временные метки (`created_at`, `updated_at`) используют `TIMESTAMP WITH TIME ZONE`, значения по умолчанию `CURRENT_TIMESTAMP`.
- Денежные суммы хранятся в двух видах: `amount_minor` (целое число в копейках) и `amount` (`NUMERIC(10,2)`), для точных расчётов используем `Decimal`.
- Значения перечислений (`Enum`) хранятся в нижнем регистре (`trial`, `pending`, `yoomoney` и т. д.) в соответствии с ORM.
- Внешние ключи настроены на каскадное удаление или удержание записей, чтобы избежать «висячих» ссылок.

## Таблицы

### `plans`
| колонка | тип | описание |
| --- | --- | --- |
| `id` | `SERIAL` | surrogate PK |
| `code` | `VARCHAR(50)` | уникальный код тарифа; есть индекс `ix_plans_code` |
| `name` | `VARCHAR(100)` | публичное наименование |
| `description` | `TEXT` | описание тарифа |
| `amount_minor` | `INTEGER` | стоимость в копейках |
| `amount` | `NUMERIC(10,2)` | стоимость в рублях |
| `currency` | `CHAR(3)` | код валюты, по умолчанию `RUB` |
| `duration_days` | `SMALLINT` | длительность подписки в днях |
| `granted_quota` | `INTEGER` | количество откликов, выдаваемых тарифом |
| `is_active` | `BOOLEAN` | активен ли тариф |
| `sort_order` | `INTEGER` | порядок отображения |

### `subscriptions`
| колонка | тип | описание |
| --- | --- | --- |
| `id` | `SERIAL` |
| `user_id` | `INTEGER` FK → `users.id` (CASCADE) |
| `plan_code` | `VARCHAR(50)` FK → `plans.code` (RESTRICT) |
| `status` | `ENUM('trial','active','grace','expired','canceled')` |
| `current_period_start` | `TIMESTAMPTZ` |
| `current_period_end` | `TIMESTAMPTZ` nullable |
| `next_charge_at` | `TIMESTAMPTZ` nullable |
| `cancel_at` | `TIMESTAMPTZ` nullable |
| `cancel_at_period_end` | `BOOLEAN` |

Индексы: `ix_subscriptions_user_id`, `ix_subscriptions_plan_code`.

### `users_trials`
- Хранит информацию об активированном триале.
- Ограничения: `user_id` уникален (один триал на пользователя).
- `plan_code` FK → `plans.code` (RESTRICT).

### `payment_methods`
| колонка | тип |
| --- | --- |
| `id` | `SERIAL` |
| `user_id` | FK → `users.id` (CASCADE) |
| `provider` | `ENUM('yoomoney')` |
| `external_id` | `VARCHAR(128)` уникальный |
| `masked_pan` | `VARCHAR(32)` |
| `is_default` | `BOOLEAN` |
| `raw` | `JSONB` |

### `payments`
| колонка | тип |
| --- | --- |
| `id` | `SERIAL` |
| `user_id` | FK → `users.id` (CASCADE) |
| `plan_code` | FK → `plans.code` (RESTRICT) |
| `provider` | `ENUM('yoomoney')` |
| `payment_method_id` | FK → `payment_methods.id` (SET NULL) |
| `subscription_id` | FK → `subscriptions.id` (SET NULL) |
| `idempotency_key` | `VARCHAR(64)` уникальный |
| `provider_payment_id` | `VARCHAR(128)` уникальный |
| `amount_minor` | `INTEGER` |
| `amount` | `NUMERIC(10,2)` |
| `currency` | `CHAR(3)` |
| `status` | `ENUM('initiated','pending','succeeded','failed','canceled','expired')` |
| `invoice_pdf_url` | `VARCHAR(1024)` |
| `raw` | `JSONB` |

Индексы: `ix_payments_user_id`, `ix_payments_plan_code`.

### `payment_attempts`
- Связаны с `payments` (CASCADE).
- `provider` и `status` используют те же перечисления, что и `payments`.
- `idempotency_key` хранит ключ запроса.
- Ограничение `uq_payment_attempt_idx` на пару `(payment_id, attempt_number)`.

### `payment_events`
- Журнал событий провайдера.
- `provider_event_id` уникален.

### `application_quotas`
- `user_id` FK → `users.id` (CASCADE), уникален.
- `plan_code` FK → `plans.code` (SET NULL).
- Содержит ежедневные и триальные лимиты и расход.

### `settings`
- Хранит пользовательские настройки (рабочее окно, фильтры).
- `user_id` уникальный FK → `users.id` (CASCADE).

### `companies_blacklist`
- Черный список компаний по пользователю (CASCADE, индекс по `user_id`).

### Дополнительно
- В `search_queries` добавлено поле `updated_at` (`TIMESTAMPTZ`).
- Все перечисления синхронизированы с ORM-классами (`Provider`, `PaymentStatus`, `SubscriptionStatus`).

## Сидовые данные
Миграция `p1_1_seed_default_plans` и скрипт `backend/seed_dev.py` создают три тарифа:

| Код | Название | Стоимость | Квота |
| --- | --- | --- | --- |
| `FREE_TRIAL` | Free Trial | 0 ₽ | 10 откликов |
| `WEEKLY` | Weekly | 990 ₽ | 200 откликов |
| `MONTHLY` | Monthly | 2990 ₽ | 800 откликов |

Эти значения синхронизированы между миграцией и скриптом сидов.
