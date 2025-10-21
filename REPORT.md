# Iteration 0 — отчёт

## 1. Срез структуры и инфраструктуры
- `hh-bot-public/` — основной монорепозиторий.
  - `HH бот/backend/` — FastAPI-приложение, async SQLAlchemy (`core/db.py`), платежный сервис YooMoney (`services/billing.py`, `payments/`), alembic-модели и миграции.
  - `HH бот/bot/` — телеграм-бот, entrypoint в `entrypoint.sh`.
  - `admin_front/` и `HH бот/adminka/` — фронтенд админки (Vite/React + статика).
  - `nginx/` — конфиги обратного прокси и basic auth.
  - `docker-compose*.yml`, `Dockerfile` — мультистейдж (web/bot), профили для prod/dev/windows.
  - `secrets/` — файловые секреты для cloudflared/YooMoney/HH OAuth.
  - `docs/`, `ops/`, `tools/` — runbooks, диагностика, GitHub Actions (`.github/workflows/ci-cd.yml`).
- Docker-стек: `web` (FastAPI), `bot`, `db` (Postgres 16), `cache` (Redis 7), `nginx`, `cloudflared`; общие политики безопасности в `docker-compose.prod.yml`.
- CI: линтеры (`ruff`, `mypy`, `pytest`) и публикация образов в GHCR, деплой через SSH.

## 2. Среды и конфиги
- `.env`, `.env.local`, `.env.dev`, `.env.prod` + `env.example*`; секреты прод-уровня лежат в `secrets/*.txt`.
- `settings` (Pydantic) читают SECRET_KEY и ADMIN_SECRET_TOKEN как обязательные; Redis + Postgres URL берутся из env.
- В `docker-compose.prod.yml` сервисы монтируют `/run/secrets/...`; включены health-check'и `curl`/`wget`.
- `run-cloudflared.ps1`, `docker-compose.prod.local.yml` — вспомогательные скрипты для туннеля и локального запуска.

## 3. Статический анализ и тестовые проверки
| Шаг | Результат | Комментарий |
| --- | --- | --- |
| `python3 -m pip --version` | ❌ `No module named pip` | Системный Python 3.12.3 поставлен без `pip/ensurepip`, поэтому установка зависимостей невозможна. |
| `python3 -m venv .venv` | ❌ `ensurepip is not available` | Создание виртуального окружения заблокировано. |
| `ruff --version`, `black --version`, `mypy --version` | ❌ `command not found` | Линтеры отсутствуют; установить без `pip` нельзя. |
| `docker compose -f docker-compose.prod.yml config` | ✅ | Конфигурация синтаксически валидна. |
| `docker compose up` | ⏸️ Не запускался | Запуск без правок `.env.prod` небезопасен, т.к. в нём лежат боевые токены; запуск с `.env.local` требует недостающих миграций. |

## 4. Выявленные риски и долги
- **Компрометация секретов**: `.env.prod` содержит приватные токены (`TELEGRAM_BOT_TOKEN`, `CF_TUNNEL_TOKEN`, реальные пароли Neon). Их наличие в git — критический риск, требуют немедленного выноса в секрет-хранилище + ротацию.
- **Миграции**: активная миграция `20250924_unify_schema.py` не синхронизирована с новыми требованиями тарифов; отсутствуют таблицы `plans`, `application_quotas` и пр.
- **Кодовая база**: `models.py` схлопывает все модели в один файл, старые директории `app/models/*` удалены; потребуется ревизия импорта и Alembic автогенерации.
- **Аналитика/логирование**: отсутствуют события `trial_*`, нет трассы UTM → TG → backend.
- **Инфраструктура**: Cloudflare туннель завязан на один токен без fallback; нет health-check'ов для `cloudflared` в CI, только runtime.
- **Observability**: нет сбора метрик/логов для платежных ретраев; `structlog` только в части кода.
- **Тестовый контур**: `pytest` не запускался из-за отсутствия зависимостей; необходимо восстановить возможность локального запуска (pip/venv).

## 5. Отсутствующие данные / вопросы на уточнение
1. Подтвердить, что продовые токены из `.env.prod` уже отозваны и будут заменены (иначе работу надо остановить).
2. Требуется ли поддержка существующих кодов плана (`premium-month`) при миграции на новую матрицу (FREE_TRIAL/WEEKLY/MONTHLY)?
3. Где canonical-источник тарифов — backend или фронт (админка), нужна ли синхронизация с UI?
4. Есть ли актуальные диаграммы БД/Alembic (последний артефакт `_artifacts/_alembic.txt` датирован 2025-10-05)?
5. Для итерации 0 допускается запуск стека на `.env.local` без внешних интеграций, или требуется полноценный прод-режим (что небезопасно)?
6. Нужен ли `ASSUMPTIONS.md` для фиксации допущений, или достаточно вести их в `REPORT.md`?

## 6. Рекомендации перед Iteration 1
- Восстановить инструменты: установить `python3-venv`/`pip` либо предоставить контейнер/Poetry для локальных проверок.
- Немедленно удалить/ротация секретов из `.env.prod`, перевести на `.env.prod.template` + `secrets`/CI variables.
- Согласовать схему тарифов и ограничения квот до проектирования миграций.
- Проверить доступ к Neon/Redis (SSL requirements) перед написанием сидов и миграций.
- Решить, где фиксируем продуктовые решения (создать `DECISIONS.md`, как просили в маршрутной карте).

Готов приступить к Iteration 1 после получения ответов на вопросы и разблокировки статических проверок.
