# GAP_REPORT
## Сводка
- Критичные блокеры P0: продовые секреты в `.env.prod` (надо вынести/ротировать), отсутствует тарифная схема (`plans/subscriptions/...`), платежный флоу YooMoney без идемпотентности/ретраев, инфраструктура публикации (cloudflared/nginx/DNS) не доведена до DoD.
- Основные риски: кодовая база исторически без линтеров/типов (мягко заглушили mypy, нужно поэтапно включать), тестовый контур ограничен (pytest зелёный, но покрывает не всё), базовые runbooks/наблюдаемость отсутствуют.

## Матрица (Yes/No/Partial)
| Раздел | Статус | Риск | Что сделать |
|-------|--------|------|-------------|
| Code health | Partial | Ранее отсутствовали автоформат/линты/типы; сейчас `dev_check` зелёный, но mypy заглушён `ignore_errors`, предстоит вернуть строгие проверки на новых модулях | Зафиксировать постепенное ужесточение mypy (module overrides), добавить целевые тесты; вернуть строгие правила по мере рефакторинга |
| DB/миграции | No | Нет таблиц `plans/subscriptions/payments/application_quotas`, миграции устарели | P0-3: спроектировать модели и Alembic-миграции, seed тарифов, обратимость |
| YooMoney | No | Нету идемпотентности/ретраев/статусов; риск двойных списаний | P0-5: внедрить idempotency_key, таймауты с backoff, события `payment_*`, интеграционные тесты |
| Тарифы/квоты | No | FREE_TRIAL/WEEKLY/MONTHLY не реализованы; квоты отсутствуют; «Откликнуться» не проверяет статус | P0-3/4: таблицы + сервис квот, эндпоинты `trial/activate`, списание при отклике |
| .env/секреты | No | Боевые значения в `.env.prod`, нет контроля утечек | P0-2: вынести в плейсхолдеры, включить gitleaks/pre-commit, fail-fast и задачи на ротацию |
| Инфра | Partial | Docker prod работает, но security headers/healthz/cloudflared http2 надо перепроверить | P0-6: ревизия nginx (timeouts/headers), cloudflared (`--protocol http2`), docker-prod чек-лист |
| DNS/CF | Partial | Требуется подтвердить CNAME → *.cfargotunnel.com, настроить WAF/split-tunnel | P0-6: проверить записи и исключения TLS-инспекции, обновить документацию |
| Наблюдаемость | No | Нет метрик/алертов, структурные логи частично | P1: собрать метрики RPS/латентность/платежи, подключить alerting, логирование GoS |
| Аналитика | No | Нет трассы UTM→TG→сервер, события `trial_*`, `payment_*` не пишутся | P1: внедрить события и эталон выгрузки |
| Безопасность | Partial | rate limiting/PII маскирование не проверены | Аудит критичных эндпоинтов, добавить лимиты и маскировку |
| Runbooks | No | Нет документации по деплою/откату/инцидентам | P1: написать RUNBOOK.md и сценарии аварий |
| Право | Partial | Требуются обновлённые тексты оферты/повторных списаний | Синхронизировать с юристами, добавить уведомления в Paywall и письма |

## Детали и логи
LOG_SUMMARY: `docker compose -f docker-compose.dev.yml up --build app` — `dev_check` создаёт .uv-окружение, синхронизирует `requirements-all.txt`, запускает `ruff/black/mypy/pytest`; все команды успешны.  
LOG_SNIPPET (≤40): ```
[dev_check] Python:
Python 3.12.12
[dev_check] Установка зависимостей проекта:
Using Python 3.12.12 environment at: .uv
Resolved 70 packages in 5.18s
Installed 45 packages in 4.93s
[dev_check] Установка инструментов (ruff, black, mypy, pytest, alembic) через uvx:
[dev_check] Линтеры/типы/тесты:
All checks passed!
Success: no issues found in 76 source files
.........                                                                [100%]
9 passed, 3 warnings in 37.80s
[dev_check] Compose sanity (db/redis доступность):
db: True redis: True
```
