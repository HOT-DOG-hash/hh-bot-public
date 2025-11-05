# LOCAL_DEV

## Prerequisites
- Windows 10/11 with Docker Desktop (tested on Docker 28.4.0 / Compose v2.39.4).
- PowerShell 5+ or 7+ with access to `docker`, `curl`, and repo scripts under `tools/`.
- Work from `C:\git-public\hh-bot-public` with an elevated shell (right-click -> Run as administrator).

## Environment Files
1. Copy `.env.local.sample` to `.env.local` on first run (safe to overwrite when sample updates).
2. Dev defaults already set:
   - `DATABASE_URL=postgresql+asyncpg://hh:devpass@db:5432/hh`
   - `REDIS_URL=redis://cache:6379/0`
   - `WEB_PORT=8000`
   - `SECRET_KEY=local-dev-secret`
   - `ADMIN_USER=admin`, `ADMIN_PASS=devadmin`, `ADMIN_SECRET_TOKEN=local-dev-admin-token`
   - `LOG_FILE=logs/app.log`, `BOT_LOG_FILE=logs/bot.log`
   - `ENABLE_TELEGRAM_BOT=0`
   - `VITE_API_BASE=https://localhost:8443/api`
   - `VITE_USE_MOCKS=0`
   - `TZ=UTC`
3. Keep `.env.local.sample`, `env.example*` in sync with new variables; never commit real secrets.

## Dev Certificates
```
pwsh tools\dev-cert-gen.ps1
```
- Generates or refreshes `opt/dev-cert/live/localhost/{fullchain.pem,privkey.pem}`.
- Uses local OpenSSL when available, falls back to Docker (`alpine/openssl`) otherwise.
- Idempotent; rerun when certificates expire or are missing.

## HTTP Ports
```
pwsh tools\set-nginx-ports.ps1
```
- Checks whether 80/443 are free. Keeps default bindings `127.0.0.1:80/443` when available, switches to `127.0.0.1:8080/8443` only if required.
- Creates timestamped backups before editing `docker-compose.override.yml`.

## Starting the Stack
```
docker compose --env-file .\.env.local up -d db cache
# wait for healthy
docker compose --env-file .\.env.local up -d web front nginx
```
- Avoid `docker compose down -v`; prefer `docker compose restart <svc>` for troubleshooting.
- `front` image builds the SPA inside a node:20-alpine stage and syncs `/opt/dist` into the named volume `front_dist`.

## Database Migrations
```
docker compose --env-file .\.env.local exec -T web alembic upgrade head
docker compose --env-file .\.env.local exec -T web alembic current
```
- Head as of 2025-10-05: `20250924_unify_schema` (see `_artifacts/_alembic.txt`).

## Health Checks
```
curl -s -o NUL -w "%{http_code}" http://localhost:80/healthz
curl -k -s -o NUL -w "%{http_code}" https://localhost:443/api/health
curl -k -u admin:devadmin -s -o NUL -w "%{http_code}" https://localhost:443/admin/
```
- Expect 200 for all endpoints (HTTP `/admin` will 301 to HTTPS before auth challenge).
- If `set-nginx-ports.ps1` switched to 8080/8443, replace ports accordingly.
- Update `nginx/.htpasswd` after credential changes via `pwsh .\htpasswd-set.ps1 -User <admin> -Password <pass>`.

## Admin Frontend (Vite React)
- Source lives in `admin_front/` (Vite + React + TypeScript + Tailwind + shadcn/ui + Recharts).
- Useful scripts:
  - `npm run dev` (port 5173, proxies `/api`).
  - `npm run build`, `npm run preview`, `npm run lint`, `npm run typecheck`, `npm run gen:shadcn`.
- Container build: `docker compose build front` (requires internet for npm install).
- Static files land in the `front_dist` volume and are served by nginx from `/admin` behind BasicAuth.
- Toggle mock data with `VITE_USE_MOCKS` until backend endpoints are ready.

## Self-Test & Artifacts
```
pwsh tests\front-selftest.ps1
```
Produces `_front_http.txt`, `_front_ps.txt`, `_front_nginx.log`, `_front.log` under `_artifacts/`.

Full stack smoke (db/cache/web/nginx):
```
pwsh tests\deploy-selftest.ps1
```
Generates `_compose.config.txt`, `_ps.txt`, `_db.log`, `_web.log`, `_nginx.log`, `_alembic.txt`, `_http.txt`, and `tree.txt`.

## Git Notes
- Run `git status` / `git fsck --no-dangling` before committing; current repo shows pack/index corruption (see `_artifacts/_git.txt`).
- Repair via `git gc --prune=now && git repack -a -d` or reclone afresh and copy your worktree.
- `.gitignore` already excludes `_artifacts/`, `opt/dev-cert/`, `admin_front/node_modules/`, and build outputs.
