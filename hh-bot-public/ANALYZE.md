# ANALYZE.md тАУ repository audit (2025-10-12)

## Summary
- Sanitised every `.env*`/`env.example*` file; no production credentials remain in Git.
- Default configs now declare all required keys (`ADMIN_BASIC_REALM`, log paths, access token TTL, etc.) so `pydantic-settings` validation no longer falls back to SQLite.
- Local docker stack still targets ports 80/443 with HTTPS served by nginx; `cloudflared` remains optional and now defaults to disabled without a token.
- Admin SPA builds into the `front_dist` volume and is proxied behind BasicAuth (`admin/devadmin` in dev).
- Git history previously reported pack corruption; recloning or `git gc` is still recommended before long-term work.

## Environment Matrix
| file | purpose | key values |
| --- | --- | --- |
| `.env` | baseline for docker-compose/prod | placeholder secrets, logging to `/var/log/app`, bot disabled |
| `.env.local` | docker dev | `devpass` DB, `logs/` targets, `ADMIN_SECRET_TOKEN=local-dev-admin-token`, mocks off |
| `.env.dev` | legacy tooling alias | mirrors `.env.local` |
| `.env.prod` | deployment scaffold | `CHANGE_ME_*` placeholders, no real tokens |
| `.env.local.sample` | bootstrap | copy instructions for new contributors |
| `env.example*` | standalone templates | aligned with the above (dev/prod variants) |
| `admin_front/.env.example` | SPA mock defaults | unchanged (uses `https://localhost:8443/api`) |

All sensitive values must be supplied via secrets manager or local overrides before deploying.

## Docker Topology
- `db` (PostgreSQL 16) and `cache` (Redis 7) expose only internal ports.
- `web` (FastAPI) pulls credentials from `.env*` and writes logs to `/var/log/app` (mounted volume).
- `front` builds the admin SPA; output served by `nginx` at `/admin` with BasicAuth.
- `cloudflared` is optional; do not enable without providing `CF_TUNNEL_TOKEN`.

## Health Expectations
| endpoint | expected | notes |
| --- | --- | --- |
| `http://localhost/healthz` | 200 | simple readiness |
| `https://localhost/api/health` | 200 | requires dev TLS cert (use `-k`) |
| `https://localhost/admin/` | 200 | supply BasicAuth `admin/devadmin` |

## Outstanding Risks
1. Docker Desktop stability issues previously observed; rerun stack smoke-tests after restarting Docker.
2. Git pack/index corruption reported earlier (`_artifacts/_git.txt`); prefer fresh clone before further commits.
3. Lighthouse automation still needs a robust command wrapper (current reports land in `_artifacts/` when run manually).

## Next Steps
1. Recreate `.env.local` from the sample, inject real secrets via `.env.override` or secrets manager.
2. Run `docker compose --env-file .\.env.local up -d db cache web front nginx`.
3. Execute `docker compose exec -T web alembic upgrade head` and `pytest`.
4. Capture updated `_artifacts` (compose config, health checks, docs snapshots).
