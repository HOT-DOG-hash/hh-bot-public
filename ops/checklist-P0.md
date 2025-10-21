# GO/NO-GO Checklist — P0

- [x] Alembic tree unified (`backend/migrations`); dry-run `alembic upgrade head` on test copy succeeds.
- [x] `/health` returns HTTP 200 when Postgres/Redis healthy and 503 when either dependency fails; `/healthz` stays 200.
- [x] Persistent volume `resumes` attached; file writes survive `docker compose restart web`; retention job configured (30d).
- [x] `/opt/app/.env` and `nginx/.htpasswd` mode 600; BasicAuth on `/admin/*` returns 401 without creds and 200 with valid creds.
- [x] HTTPS active, HTTP→HTTPS redirect; `certbot renew --dry-run` + systemd timer succeed.
- [x] Container healthchecks (web/bot/nginx) green; bot waits for DB/Redis before polling.
- [x] Firewall only exposes TCP/80 and TCP/443 (ufw `status verbose`).
- [x] `ops/smoke.sh` passes before/after simulated DB outage; `/health` → 503 while DB down.
