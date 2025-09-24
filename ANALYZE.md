# ANALYZE.md — Теханализ и статус проекта (дата: 2025-09-24)

## A. EXECUTIVE SUMMARY
- Вердикт: NO-GO — остались невыполненные P0: `alembic -c alembic.ini heads` падает из-за пути с кириллицей, а certbot-renew не перезагружает nginx после обновления сертификатов.
- Топ P0 рисков:
  1. Alembic CLI не находит каталог `HH бот/backend/migrations`, миграции не прогоняются автоматически.
  2. Сервис `certbot-renew.service` не перезапускает nginx после `renew`, возможен устаревший сертификат в памяти.
  3. У web-контейнера сохраняется read-only rootfs, что усложняет запись вне размонтированных томов.

## B. КАРТА СИСТЕМЫ (кратко)
- Сервисы: nginx (reverse proxy + Cloudflare real IP), web (FastAPI + Alembic), bot (PTB long-polling), db (Postgres 16), cache (Redis 7), cloudflared tunnel, certbot/systemd helpers, ops/* scripts.
- Наружные порты: 80/443 (localhost bind, вход из Cloudflare). cloudflared использует `network_mode: service:nginx`.
- Томa: `pgdata`, `redisdata`, `web_logs`, `botlogs`, `resumes`, tmpfs `/tmp`, `/var/cache/nginx`.
- Сеть: docker default bridge + Cloudflare туннель.

## C. ЧТО РЕАЛИЗОВАНО (по факту кода)
- Миграции: единое дерево `HH бот/backend/migrations`, ревизия `20250924_unify_schema.py`, индексы и `uq_users_tg_id` — ✅
- Lazy-init БД + startup ping — ✅
- /health (503 при деградации) / /healthz — ✅
- Персистентность резюме + ретеншн — ⚠ (том есть, cron-скрипт есть, но web остаётся `read_only: true`)
- Nginx: CF real IP, TLS, 80→443, body-size 25m, HSTS/OCSP — ✅
- Certbot renew + reload nginx — ⚠ (есть таймер, но нет reload nginx)
- Секреты/BasicAuth — ✅
- CI/CD workflow — ✅ (`.github/workflows/ci-cd.yml`)
- Наблюдаемость/прочее (Sentry, Prometheus, webhook, auto-alembic) — ⚠

### Implemented (по коду)
- `HH бот/backend/migrations/versions/20250924_unify_schema.py` — консолидированная миграция и перенос legacy ✅
- `backend/app/core/db.py:get_engine()` — ленивое создание движка ✅
- `backend/app/main.py:113-133` — startup ping Postgres ✅
- `backend/app/routers/health.py` — HTTP 503 при сбоях DB/Redis, `/healthz` = 200 ✅
- `docker-compose.yml` / `docker-compose.prod.yml` — healthcheck `/health`, том `resumes`, бот-хелсчек ✅
- `nginx/nginx.conf` — Cloudflare CIDR, HSTS, OCSP, body-size ✅
- `ops/prepare-secrets.sh` — генерация секретов без утечки ✅
- `ops/cleanup-resumes.sh` + инструкции в `ops/runbooks.md` — retention скрипт ✅
- `ops/systemd/certbot-renew.service` + `.timer` — таймер есть, reload отсутствует ⚠

## D. P0 — НАЙДЕННЫЕ РИСКИ/ДОЛГ
| # | Риск/несоответствие | Почему критично | Доказательство (файл/строка) | Фикс (конкретно) | ETA |
|---|---|---|---|---|---|
| 1 | `alembic -c alembic.ini heads` падает: «Path doesn't exist…» | Без автопрогонов миграций любая поставка схемы сорвётся | `alembic.ini:6`, команда `py -3 -m alembic -c alembic.ini heads` | Перенести migrations в ASCII-путь или обновить `script_location` (например `backend/migrations`) и проверить на CI | ASAP |
| 2 | `certbot-renew.service` не перезапускает nginx | nginx продолжает обслуживать старый сертификат после renew | `ops/systemd/certbot-renew.service` | Добавить wrapper `/usr/local/bin/hh-certbot-renew` с `docker compose exec nginx nginx -s reload`, обновить unit/timer | ASAP |
| 3 | web-контейнер наследует `read_only: true` из `*common_secure` | Ограничивает запись вне заранее смонтированных томов (pip/миграции) | `docker-compose.yml`, `docker-compose.prod.yml` | Убрать `read_only` из web (и при необходимости bot), оставить точечные tmpfs/volumes | ASAP |

## E. P1/P2 — РЕКОМЕНДАЦИИ ПОСЛЕ РЕЛИЗА
- P1: включить CI/CD (секреты GHCR, deploy), настроить Cloudflare proxy/WAF, ввести ресурсные лимиты, поднять staging + nightly smoke.
- P2: webhook-режим бота (secret/IP whitelist), Sentry + Prometheus `/metrics`, Dependabot/Renovate, auto-`alembic upgrade head`, улучшенный retention (метки «immutable»).

## F. ДОКАЗАТЕЛЬНАЯ БАЗА (команды/выводы)
```bash
$ rg -n "script_location" alembic.ini
6:script_location = HH бот/backend/migrations

$ py -3 -m alembic -c alembic.ini heads
FAILED: Path doesn't exist: 'C:\\git-public\\hh-bot-public\\HH бот\\backend\\migrations'

$ rg -n "set_real_ip_from" nginx/nginx.conf
34:set_real_ip_from 173.245.48.0/20
...
100:add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always

$ rg -g 'docker-compose*.yml' -n 'resumes'
docker-compose.yml:88:- resumes:/app/media/resumes
docker-compose.prod.yml:67:- resumes:/app/media/resumes

$ rg -n "certbot-renew" ops/systemd
ops/systemd/certbot-renew.service:8:ExecStart=/usr/bin/docker run --rm ... certbot/certbot renew --quiet
```
