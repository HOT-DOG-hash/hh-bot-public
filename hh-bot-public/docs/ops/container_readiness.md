# Container Readiness Guide

## Target Images
- Web & Bot: `python:3.11-slim` (update yearly; evaluate 3.12 when stable).
- Database: `postgres:16-alpine`.
- Cache: `redis:7-alpine`.

## Health / Readiness
- Web healthcheck: `curl http://127.0.0.1:${WEB_PORT}/health` (HTTP 200).
- Dependencies: Postgres (`pg_isready`) and Redis (`redis-cli ping`) defined in docker-compose.
- Bot readiness: ensure entrypoint script connects to DB/Redis; monitor log `bot.log`.

## Security Notes
- Compose uses `read_only: true`, `tmpfs /tmp`, `cap_drop: ALL` for web/bot.
- Logging driver: json-file (10m size, x5 files, compressed).

## Release Steps
1. Build images via Dockerfile targets `web` and `bot`.
2. Run `docker-compose` (prod overrides) and wait for healthchecks.
3. Verify `/readyz` and `/metrics` endpoints within container.
4. After release, monitor alerts per `docs/dashboards/ACCEPTANCE.md` for 24h.
