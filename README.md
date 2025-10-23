# hh-bot-public

Продуктовое окружение для HH Bot: веб API на FastAPI, телеграм-бот, nginx как обратный прокси и Cloudflare Tunnel для публикации доменов `hhoffer.ru`, `www.hhoffer.ru`, `api.hhoffer.ru`.

## Архитектура
- **web** — FastAPI-приложение (`backend.app.main:app`), отвечает за REST API и `/health`.
- **bot** — сервис фоновых задач и Telegram-бот.
- **nginx** — reverse proxy, обслуживает SPA-админку и проксирует `/api/` к FastAPI; health-check `/healthz`.
- **db / cache** — PostgreSQL 16 и Redis 7.
- **cloudflared** — Cloudflare Named Tunnel (HTTP/2, IPv4) к `nginx:80`.

## Требования
- Docker Desktop 28+ (Compose v2).
- PowerShell 7+.
- Подготовленный `.env` (на основе `.env.example`) с реальными секретами, хранимыми вне репозитория (ENV/CI vault).

## Быстрый старт (Docker)
1. Скопируйте шаблон окружения и заполните значения:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Запустите стек:
   ```powershell
   docker compose -f docker-compose.prod.yml up -d --build
   ```
3. Проверьте статусы:
   ```powershell
   docker compose -f docker-compose.prod.yml ps
   docker compose -f docker-compose.prod.yml logs nginx
   ```
4. Локальный доступ:
   - `http://127.0.0.1` — статический фронт.
   - `http://127.0.0.1/admin/` — SPA админка (basic auth).
   - `http://127.0.0.1/healthz` — health-check nginx.

## Локальная разработка backend
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```
Используйте `.env.local` (или `.env.local.sample`) для dev-значений.

## Smoke-тесты backend
- `python -m pip install -r requirements.txt`
- `pytest -q` — полный smoke-набор с моками YooMoney и HeadHunter.
- Точечные проверки: `pytest tests/test_billing_smoke.py -q`, `pytest tests/test_hh_oauth_jobs.py -q`.
- Прод-роуты для ручной валидации:
  `curl -I "https://api.hhoffer.ru/oauth/hh/login?chat_id=<CHAT_ID>"`
  `curl -sS "https://api.hhoffer.ru/billing/subscription" -H "X-User-Id: <USER_KEY>"`

## Команды CI локально
- `python -m pip install --upgrade pip && pip install ruff mypy`
- `ruff check .`
- `mypy --ignore-missing-imports .`
- `pytest -q` или `make test`

## Секреты и конфигурация
- Храните реальные значения только в ENV/CI vault. Командой `Copy-Item .env.example .env` создайте локальный шаблон и замените `CHANGE_ME`.
- В репозитории все `.env*` игнорируются; при старте приложение валидирует значения и падает, если остались плейсхолдеры либо утёкшие токены.
- Локальный и CI-скан (`pre-commit`, gitleaks) блокируют коммиты с секретами. Перед пушем выполните `uvx pre-commit run --all-files`.
- Письменно фиксируйте ротацию: Cloudflare Tunnel, YooMoney, Telegram Bot, Neon/Postgres.

## Основные маршруты backend
- `GET /healthz` — health-check сервиса.
- `POST /billing/create` — выдача ссылки на оплату (заголовок `X-User-Id`).
- `GET /billing/status/{external_id}` — сверка платежа и активация подписки.
- `GET /billing/subscription` — состояние премиума.
- `POST /api/v1/trial/activate` — запуск триала (10 откликов).
- `GET /api/v1/quota` — текущий остаток квоты/подписки.
- `POST /api/v1/apply` — отклик с проверкой квоты и идемпотентностью.
- `GET /oauth/hh/login` — старт OAuth HH (302 на hh.ru, сохраняет state в Redis).
- `GET /oauth/hh/callback` — обмен кода на токены HH и привязка профиля.
- `GET /jobs/search` — вакансии HH, работает только с активной подпиской и валидным токеном.

## Cloudflare Tunnel
`run-cloudflared.ps1` автоматизирует запуск контейнера `cloudflared` с протоколом HTTP/2:
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\run-cloudflared.ps1
```
Скрипт запросит `CF_TUNNEL_TOKEN`, если он не задан, и будет опрашивать логи до появления строк вида:
```
Registered tunnel connection
Connection registered
Connected to <edge> protocol=http2
```
При отсутствии регистрации за 120 секунд вернёт `FAIL: TLS handshake blocked (VPN/DPI?)`.

## Требования сети
- Исключите из VPN и HTTPS-инспекции домены `region*.v2.argotunnel.com`, `*.cfargotunnel.com`.
- Разрешите исходящий трафик в обход VPN:
  - TCP/443 (обязательно) и UDP/7844 (желательно).
  - IPv4 сети Cloudflare: `198.41.192.0/24`, `198.41.200.0/24`.
  - При использовании IPv6: `2606:4700:a0::/48`, `2606:4700:a8::/48`.
- Типичные симптомы блокировки: записи вида `TLS handshake ... EOF` в логах `cloudflared`, TLS alert при обращении к `https://region1.v2.argotunnel.com/cdn-cgi/trace`.
- Минимальный набор проверок доступа:
  1. Запуск `run-cloudflared.ps1` и ожидание `Registered tunnel connection`.
  2. Проверка DNS: `nslookup -type=cname www.hhoffer.ru 1.1.1.1` и `nslookup -type=cname api.hhoffer.ru 1.1.1.1`.
  3. Внешние health-checkи: `Invoke-WebRequest https://hhoffer.ru/healthz -UseBasicParsing` (и аналогично для `www`, `api`).

## Проверка продового доступа
```powershell
Invoke-WebRequest https://hhoffer.ru/healthz -UseBasicParsing
Invoke-WebRequest https://www.hhoffer.ru/healthz -UseBasicParsing
Invoke-WebRequest https://api.hhoffer.ru/healthz -UseBasicParsing
```
Из Docker-сети:
```powershell
docker run --rm --network hh-bot-public_default curlimages/curl:8.10.1 -si http://nginx/healthz
```
Ожидается `HTTP/1.1 200 OK` и тело `ok`.

## Деплой чек-лист
1. Обновить секреты в vault (DATABASE_URL, REDIS_URL, TELEGRAM/YOOMONEY токены, CF_TUNNEL_TOKEN) и раздать окружениям.
2. Пересобрать образы (при необходимости) и выполнить `docker compose -f docker-compose.prod.yml up -d`.
3. Запустить `run-cloudflared.ps1` и убедиться, что туннель зарегистрирован.
4. Проверить Published Application Routes в Cloudflare Zero Trust: `hhoffer.ru`, `www.hhoffer.ru`, `api.hhoffer.ru` → `http://nginx:80`, Path пустой.
5. Прогнать health-checkи и smoke-тесты ручным curl или `Invoke-WebRequest`.
6. Проверить логи `cloudflared`, `nginx`, `web` на наличие 4xx/5xx и завершить релиз.

## Миграции тарифов
- `alembic revision -m "p0-3 billing schema"` — создать ревизию (дальше правим вручную).
- `alembic upgrade head` — применить схему `plans/subscriptions/payments/application_quotas`.
- `alembic downgrade -1` — откатить последнюю миграцию.
- `make dev-up` — поднять dev-стек (db/redis + приложение).
- `make dev-test` — запустить pytest в dev-контейнере.
- `docker compose -f docker-compose.dev.yml up --build app` — альтернатива без Makefile.

## Payments API
-  `POST /api/v1/payments/initiate` — создание платежа с идемпотентностью по `idempotency_key`. 
-  `POST /api/v1/payments/webhook` — приём и дедупликация вебхуков YooMoney. 
-  `GET /api/v1/payments/{id}/status` — финальный статус платежа и `next_charge_at`. 
