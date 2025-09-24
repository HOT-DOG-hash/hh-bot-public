# Репозиторий hh-bot-public — обзор

## Обзор
- Monorepo с основным Python-фреймворком: `HH бот/backend` (FastAPI + Telegram bot), `HH бот/bot` (отдельный runner), фронты `HH бот/adminka` (SPA под nginx), `HH бот/front_bot` (Python телеграм-клиент) и `HH бот/front_bot_php` (legacy PHP).
- Обвязка инфраструктуры: docker-compose файлы для Linux/Windows/prod/Neon, reverse-proxy `nginx`, облачный туннель `cloudflared`, stateful сервисы `db` (PostgreSQL) и `cache` (Redis).
- Скрипты PowerShell/Makefile для администрирования, диагностический пакет `diag_bundle`, артефакты безопасности в `tools/reports`.
- Тесты лежат в `HH бот/backend/tests` (pytest + httpx), что подтверждает FastAPI-стек.

## Дерево (первые 120 строк)
```text
./
  .github/
    .github\hooks/
      .github\hooks\pre-commit
    .github\workflows/
      .github\workflows\ci-cd.yml
      .github\workflows\secrets-scan.yml
  alembic/
    alembic\versions/
    alembic\env.py
    alembic\README
    alembic\script.py.mako
  diag_bundle/
    diag_bundle\diag_report.json
    diag_bundle\docker-compose.yml
    diag_bundle\Dockerfile
    diag_bundle\nginx.conf
  front_bot/
    front_bot\routers/
      front_bot\routers\start.py
  HH бот/
    HH бот\adminka/
      HH бот\adminka\index.html
      HH бот\adminka\script.js
      HH бот\adminka\styles.css
      HH бот\adminka\user-profile.html
      HH бот\adminka\user-profile.js
    HH бот\backend/
      HH бот\backend\alembic/
        HH бот\backend\alembic\versions/
          HH бот\backend\alembic\versions\20250828_init.py
      HH бот\backend\app/
        HH бот\backend\app\core/
          HH бот\backend\app\core\__init__.py
          HH бот\backend\app\core\config.py
          HH бот\backend\app\core\db.py
          HH бот\backend\app\core\logging.py
          HH бот\backend\app\core\redis.py
        HH бот\backend\app\models/
          HH бот\backend\app\models\schemas/
            HH бот\backend\app\models\schemas\__init__.py
            HH бот\backend\app\models\schemas\resume.py
            HH бот\backend\app\models\schemas\user.py
          HH бот\backend\app\models\__init__.py
          HH бот\backend\app\models\base.py
          HH бот\backend\app\models\resume.py
          HH бот\backend\app\models\user.py
        HH бот\backend\app\routers/
          HH бот\backend\app\routers\admin_api/
            HH бот\backend\app\routers\admin_api\__init__.py
            HH бот\backend\app\routers\admin_api\broadcasts.py
            HH бот\backend\app\routers\admin_api\metrics.py
            HH бот\backend\app\routers\admin_api\users.py
          HH бот\backend\app\routers\bot_api/
            HH бот\backend\app\routers\bot_api\__init__.py
            HH бот\backend\app\routers\bot_api\resume.py
            HH бот\backend\app\routers\bot_api\search.py
            HH бот\backend\app\routers\bot_api\stats.py
          HH бот\backend\app\routers\__init__.py
          HH бот\backend\app\routers\admin.py
          HH бот\backend\app\routers\health.py
          HH бот\backend\app\routers\resumes.py
        HH бот\backend\app\schemas/
          HH бот\backend\app\schemas\__init__.py
          HH бот\backend\app\schemas\resume.py
          HH бот\backend\app\schemas\user.py
        HH бот\backend\app\__init__.py
        HH бот\backend\app\config.py
        HH бот\backend\app\database.py
        HH бот\backend\app\main.py
        HH бот\backend\app\main.py.bak_20250829_140929
        HH бот\backend\app\main.py.bak_20250829_141723
        HH бот\backend\app\main.py.bak_20250829_141858
        HH бот\backend\app\models.py
        HH бот\backend\app\security_admin.py
        HH бот\backend\app\security.py
      HH бот\backend\migrations/
        HH бот\backend\migrations\versions/
          HH бот\backend\migrations\versions\7e848df00d1e_schema_check.py
          HH бот\backend\migrations\versions\90f3375d1ace_init_users_and_resumes.py
        HH бот\backend\migrations\env.py
        HH бот\backend\migrations\README
        HH бот\backend\migrations\script.py.mako
      HH бот\backend\tests/
        HH бот\backend\tests\conftest.py
        HH бот\backend\tests\test_health.py
        HH бот\backend\tests\test_resumes.py
        HH бот\backend\tests\test_security_admin.py
      HH бот\backend\__init__.py
      HH бот\backend\alembic.ini
      HH бот\backend\bot_runner.py
      HH бот\backend\Dockerfile
      HH бот\backend\README.md
      HH бот\backend\requirements.txt
      HH бот\backend\seed_dev.py
      HH бот\backend\test_import.py
    HH бот\bot/
      HH бот\bot\entrypoint.sh
      HH бот\bot\runner.py
    HH бот\front_bot/
      HH бот\front_bot\front_bot/
      HH бот\front_bot\routers/
        HH бот\front_bot\routers\__init__.py
        HH бот\front_bot\routers\auto_responses.py
        HH бот\front_bot\routers\letters.py
        HH бот\front_bot\routers\menu.py
        HH бот\front_bot\routers\responses.py
        HH бот\front_bot\routers\resume.py
        HH бот\front_bot\routers\search.py
        HH бот\front_bot\routers\start.py
        HH бот\front_bot\routers\stats.py
      HH бот\front_bot\utils/
        HH бот\front_bot\utils\__init__.py
        HH бот\front_bot\utils\buttons.py
        HH бот\front_bot\utils\helpers.py
        HH бот\front_bot\utils\states.py
        HH бот\front_bot\utils\texts.py
      HH бот\front_bot\__init__.py
      HH бот\front_bot\config.py
      HH бот\front_bot\demo_bot_persistence
```
Полный список: `tree.txt`.

## Docker/Compose
- Базовый `docker-compose.yml`: собирает образ из `Dockerfile`, поднимает `db` (Postgres 16), `cache` (Redis 7), `web` (uvicorn backend), `bot` (Python Telegram Bot), `nginx` (reverse-proxy) и `cloudflared` (туннель). Общие настройки безопасности через `x-common-secure`, логгирование `json-file`, отдельные volumes: `pgdata`, `redisdata`, `web_logs`, `botlogs`.
- `docker-compose.prod.yml`: переключает `web`/`bot` на заранее собранные образы из GHCR, оставляя инфраструктуру той же, healthchecks заточены под `/api/health` и бот-процесс.
- `docker-compose.neon.yml`: оверрайд для Neon – переопределяет `DATABASE_URL` на `${NEON_DATABASE_URL}`, отключает запуск Telegram-бота (`ENABLE_TELEGRAM_BOT=0`), но оставляет зависимость `web`/`bot` от `db` (Postgres) как no-op. Если запускать только с `-f docker-compose.neon.yml`, Compose выдаст `service "web" depends on undefined service "db"`, потому что базовый файл с описанием `db` не подключён. Исправление: либо запускать `docker compose -f docker-compose.yml -f docker-compose.neon.yml …`, либо добавить stub-сервис `db` в Neon-файл.
- `docker-compose.cf-http2.yml`: добавляет профиль/переопределение для cloudflared с HTTP/2 туннелем; требует `CF_TUNNEL_TOKEN`.
- Windows-специфичные файлы (`docker-compose.windows*.yml`) убирают bind-монты, подменяют volumes на tmpfs (обход ограничений NTFS) и готовят ручные entrypoint fixes.
- `_compose.effective.yaml` не сформирован: Docker CLI недоступен в текущем окружении (см. шаг 0), поэтому сводный конфиг не собран.

## Nginx
- `nginx/nginx.conf`: upstream `backend_web` указывает на `web:8000`, keepalive 32 соединения.
- Статика: `/admin/` обслуживается из `nginx/html/admin` (SPA) с кэшем на 7 дней для ассетов; `/` мапит только статический HTML/стили.
- Безопасность: BasicAuth (`/etc/nginx/.htpasswd`), `limit_req` на `/admin/`, строгие security-headers, `real_ip_header CF-Connecting-IP` для работы с cloudflared.
- Прокси: `/api/` и `/webhook` → `proxy_pass http://backend_web/`, передаются заголовки `X-Forwarded-*`, поддержан websocket upgrade. `/healthz` отдаёт plain `ok`, `/robots.txt` запрещает индексацию `/admin/`.

## Backend
- Точка входа `HH бот/backend/app/main.py`: создаёт FastAPI с `lifespan`. На старте настраивает логирование и при `ENABLE_TELEGRAM_BOT=1` запускает Telegram бота через PTB v20 (lifespan вызывает `start_bot`, хранит объект в `app.state`).
- Подключённые роутеры: `routers.admin` (Basic Auth через `require_admin`), `routers.health` (асинхронные проверки Postgres/Redis), исторические `admin_api`/`bot_api` пакеты существуют, но в `main.py` не включены (подключены только `admin` и `health`). Health-роутер экспортирует `/api/health`, `/api/healthz` и алиасы `/health`, `/healthz`.
- Основные env: `DATABASE_URL`, `REDIS_URL`, `ADMIN_USER/ADMIN_PASS`, `SECRET_KEY`, `APP_MODULE`, `WEB_PORT` (по умолчанию 8000). Лог-файлы пишутся в `/var/log/app/app.log` (см. volume `web_logs`).
- Доп. сервисы: `routers/resumes` пишет загруженные файлы в `/app/media/resumes` (локальный каталог внутри контейнера, без отдельного volume), `admin_api/broadcasts` складывает задачи в Redis-лист `broadcast_queue`, `admin_api/metrics` считает агрегаты по таблицам `users`, `search_queries` через SQL.
- `HH бот/bot/runner.py`: отдельный процесс, импортирует `start_bot/stop_bot` из backend и запускает их без FastAPI-сервера; entrypoint валидирует наличие токена и источника `.env`.

## БД и миграции
- Используются async SQLAlchemy и Alembic. Основные декларативные модели (`backend/app/models`) описывают `User` и `Resume`.
- Миграции разбросаны по двум деревьям:
  - `HH бот/backend/migrations` (Alembic async env) содержит ревизии `90f3375d1ace_init_users_and_resumes.py` и `7e848df00d1e_schema_check.py` (пустой diff). Здесь создаются таблицы `user` и `resume`, но нет `search_queries`.
  - Отдельно `HH бот/backend/alembic/versions/20250828_init.py` создаёт `users`, `search_queries`, `resumes` с колонкой `chat_id`. Этот набор несовместим по именам с основными моделями (`user/resume`, `tg_id`).
- Конфигурация `app/core/db.py` создаёт движок из `settings.database_url`, но в `Settings` значение опционально; без `DATABASE_URL` — исключение ещё при импортировании модуля.
- Тестовые данные: `seed_dev.py` и фикстуры pytest используют `get_db`.

## Зависимости (`requirements.txt`)
- FastAPI 0.111, Uvicorn 0.30, httpx 0.26, aiohttp, aiofiles.
- Бэкенд-стек: SQLAlchemy 2.0, asyncpg, Alembic 1.13.
- Кеш/клиенты: redis 5.0.
- Телеграм: python-telegram-bot 20.8.
- Инфраструктура: pydantic 2.7 + pydantic-settings, python-dotenv.
- Тесты/качество: pytest, pytest-asyncio, respx, flake8.

## P0-проблемы и next steps
1. `backend/app/core/db.py` создаёт движок со значением `settings.database_url`, которое по умолчанию `None`. Без явно заданного `DATABASE_URL` приложение рушится на импорте. Поменять на `settings.effective_database_url` или добавить дефолт.
2. Несогласованность миграций: `admin_api/metrics` ожидает таблицу `search_queries`, но активный Alembic в `backend/migrations` её не создаёт. Нужно унифицировать дерево миграций (решить, какое из двух используется, привести названия таблиц к моделям) и обновить код/SQL.
3. Загрузка резюме пишет файлы в `/app/media/resumes` без volume и с read-write файловой системой контейнера. На рестарте данные исчезнут, а в продакшне это критично. Добавить персистентный volume и политику очистки.
4. Безопасность: дефолтные `ADMIN_USER=admin`/`ADMIN_PASS=admin` и открытая basic auth в compose-файлах. Для production требуется переопределение и secret management.
5. Отсутствует автоматический health для Redis/DB в bot-runner: бот стартует, даже если зависимые сервисы недоступны; стоит усилить проверками/ретраями или использовать тот же health API.

## Ключевые конфиги
| Файл | Назначение |
| --- | --- |
| `Dockerfile` | Мульти-стейдж образ для `web` и `bot`; устанавливает python deps, настраивает entrypoint. |
| `docker-compose.yml` | Базовая оркестрация сервисов, volumes, healthchecks и безопасные флаги. |
| `docker-compose.prod.yml` | Продакшен-оверрайд с готовыми образами и теми же зависимостями. |
| `docker-compose.neon.yml` | Подключение к Neon Postgres и отключение бота; требуется вместе с базовым файлом. |
| `docker-compose.cf-http2.yml` | Настройка cloudflared в режиме HTTP/2-туннеля. |
| `docker-compose.windows*.yml` | Обход ограничений Docker Desktop/NTFS. |
| `nginx/nginx.conf` | Reverse-proxy, basic auth, proxy_pass в `web:8000`, health и статика. |
| `HH бот/backend/app/main.py` | FastAPI приложение + lifecycle Telegram бота. |
| `HH бот/backend/app/routers/health.py` | Проверки Postgres/Redis и алиасы `/health(z)`. |
| `HH бот/backend/migrations/env.py` | Конфигурация Alembic (async) для основного backend. |
| `requirements.txt` | Согласованный список зависимостей сервисов. |

## Артефакты
- `tree.txt`
- `_compose.effective.yaml` — не создан (Docker CLI недоступен в окружении)
- `ANALYZE.md`
