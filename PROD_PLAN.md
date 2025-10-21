# PROD_PLAN

## P0 — задачи к прод-запуску

### P0-1 Baseline cleanup дев-пайплайна
**Цель.** Сделать `scripts/dev_check.sh` зелёным: автоочистка `.venv`, синхронизация зависимостей, автоформат/линт, базовые настройки mypy, актуализация Make-команд.  
**Шаги.**
1. Удалить/игнорировать `.venv`, добавить `rm -rf .venv` и `unset VIRTUAL_ENV` в начало `scripts/dev_check.sh`.
2. Разнести зависимости: `requirements.txt` (runtime) + `requirements-dev.txt`, добавить `uv pip sync` в скрипт.
3. Применить `uvx black .` и `uvx ruff --fix .`, добавить `pyproject.toml` c мягкими настройками и строгими линт-правилами.
4. Запустить `uvx mypy .` с `ignore_missing_imports=true`, зафиксировать оставшиеся предупреждения.
5. Обновить README/Makefile (альтернативы для Windows без `make`).
**Команды.** `docker compose -f docker-compose.dev.yml up --build app`; либо `make dev-up`, `make dev-lint`, `make dev-type`, `make dev-test`.  
**Критерии приёмки.** `dev_check` проходит без фатальных ошибок; ruff/black — зелёные; mypy/pytest не падают (допускаются xfail’ы с Issue-ссылкой).  
**Откат.** Вернуть резервный commit; удалить изменённые deps/форматирование.

### P0-2 Гигиена секретов
**Цель.** Устранить утечки боевых секретов и предотвратить новые.  
**Шаги.**
1. Перевести `.env.prod` → `.env.example` (плейсхолдеры), добавить `.env*` в `.gitignore`.
2. Настроить `pre-commit` + `gitleaks`, запустить скан; зафиксировать Issues на ротацию всех засветившихся токенов (Cloudflare, YooMoney, Telegram, Neon, Postgres).
3. Реализовать fail-fast: при чтении конфигов проверять, что секреты не совпадают с шаблонными значениями.
**Команды.** `pre-commit install`; `pre-commit run --all-files`; `gitleaks detect --redact`.  
**Критерии приёмки.** Репо не содержит боевых секретов; gitleaks чист или есть задачи на ротацию; fail-fast и документация обновлены.  
**Откат.** Вернуть старый `.env.prod`; отключить проверку (нежелательно).

### P0-3 Схемы тарифов и квот (Alembic)
**Цель.** Ввести таблицы `plans`, `subscriptions`, `payments`, `application_quotas` с начальными данными.  
**Шаги.**
1. Спроектировать модели SQLAlchemy (код/статусы/квоты/idempotency_key/next_charge_at).
2. Создать Alembic-миграцию (upgrade + downgrade), включить seed базовых тарифов (`FREE_TRIAL`, `WEEKLY`, `MONTHLY`).
3. Обновить репозитории/DTO, написать unit-тесты моделей/CRUD на sqlite.
**Команды.** `alembic revision --autogenerate -m "plans and billing tables"`; `alembic upgrade head`; `pytest tests/test_billing_smoke.py`.  
**Критерии приёмки.** Миграция обратима; таблицы соответствуют требованиям; тесты зелёные.  
**Откат.** `alembic downgrade <prev_rev>`.

### P0-4 FREE_TRIAL/квоты и «Откликнуться»
**Цель.** Реализовать акт активации триала, контроль квот и события аналитики.  
**Шаги.**
1. Endpoint `POST /trial/activate`: проверка повтора, запись в `application_quotas` (`granted=10`, `non_renewable=true`).
2. Обновить хук «Откликнуться»: проверка квоты/статуса подписки, списание `consumed`.
3. События `trial_activated`, `trial_quota_remaining`, `trial_exhausted`; unit/integration-тесты.
**Команды.** `pytest tests/test_billing_smoke.py`; `pytest tests/test_hh_oauth_jobs.py`; специальные unit-тесты для квот.  
**Критерии приёмки.** Повторный триал невозможен; квоты списываются корректно; события логируются.  
**Откат.** Реверт триггера, восстановление состояния в БД.

### P0-5 YooMoney устойчивость
**Цель.** Гарантировать идемпотентность, ретраи и корректные статусы платежей.  
**Шаги.**
1. Убедиться в хранении `idempotency_key`, добавить повторы (409 → repeat), таймауты (backoff).
2. Состояния `pending→succeeded|canceled|expired`, события `payment_*`.
3. Контрактные тесты с моками YooMoney, структурные логи без секретов.
**Команды.** `pytest tests/test_billing_smoke.py`; интеграционный сценарий `POST /billing/create` → `GET /billing/status`.  
**Критерии приёмки.** Повторный вызов не создаёт дубли; статусы обновляются корректно; логирование без токенов.  
**Откат.** Реверт изменений; откат миграций (если затронуты).

### P0-6 Инфра публикации
**Цель.** Подготовить прод-стек: docker, nginx, cloudflared, health-check, DNS.  
**Шаги.**
1. Проверить `docker-compose.prod.yml`, nginx-конфиги, добавить security headers, таймауты, gzip.
2. Обновить cloudflared (`--protocol http2`, проверка токена), `/healthz`, readiness/liveness.
3. Убедиться, что DNS CNAME указывают на *.cfargotunnel.com; обновить Runbook деплоя.
**Команды.** `docker compose -f docker-compose.prod.yml config`; `docker compose -f docker-compose.prod.yml up`; `curl -I https://api.hhoffer.ru/healthz`.  
**Критерии приёмки.** Все сервисы стартуют; health-check=200; облачные настройки валидны.  
**Откат.** `docker compose -f docker-compose.prod.yml down`; восстановление старого конфига.

## P1 — задачи после запуска

- **E2E-аналитика.** Трассировка UTM → TG payload → сервер, события `view_paywall`, `click_subscribe_*`, `payment_*`, `keywords_*`, `vacancy_open`, `apply_click`, `subscription_*`, `trial_*`.  
- **Наблюдаемость/алерты.** Метрики RPS/ошибки/латентность/платежи/квоты, интеграция с alerting.  
- **Runbooks.** `RUNBOOK.md` для деплоя/отката/инцидентов, сценарии отказов YooMoney/Cloudflare/Redis.  
- **Canary и постмониторинг.** План canary (≤5%), критерии SLO, мониторинг 24–48 часов.  
- **UX/Paywall v2.** Контракты API (`init/pending/success/failed`, отмена автопродления), фронт-интеграция.  
- **Admin/Reporting.** Метрики монетизации, экспорт, ретаргет-пэйвол.
