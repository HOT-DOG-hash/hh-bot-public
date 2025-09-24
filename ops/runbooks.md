# Runbooks — hh-bot Production

## Assumptions
- Host: Ubuntu 22.04, systemd, Docker Engine + Compose v2, ufw enabled.
- Repository cloned to `/opt/app/hh-bot`.
- Secrets live in `/opt/app/.env` (mode 600) and are applied via `ops/prepare-secrets.sh`.
- Cloudflare kept in DNS-only during certificate renewals (proxy can be re-enabled afterward).

## Release / Redeploy
```bash
ssh prod 'cd /opt/app/hh-bot && git pull'
ssh prod 'cd /opt/app/hh-bot && docker compose -f docker-compose.prod.yml pull'
ssh prod 'cd /opt/app/hh-bot && docker compose -f docker-compose.prod.yml up -d'
ssh prod 'cd /opt/app/hh-bot && BASE_URL=https://hhoffer.ru bash ops/smoke.sh'
```

## First Boot
1. `git clone` into `/opt/app/hh-bot`.
2. `cd /opt/app/hh-bot && sudo ENV_PATH=/opt/app/.env bash ops/prepare-secrets.sh`.
3. `docker compose -f docker-compose.prod.yml up -d`.
4. Issue certificates (section **TLS / Certbot**) and enable systemd timer.
5. Configure ufw (section **Firewall**) before opening the service publicly.

## Database migration (P0.1 dry-run)
```bash
# Backup production
PGPASSWORD="$POSTGRES_PASSWORD" docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > /backups/pre_unify_$(date +%F).sql

# Restore into sandbox DB
createdb -h 127.0.0.1 -U "$POSTGRES_USER" test_unify
psql -h 127.0.0.1 -U "$POSTGRES_USER" -d test_unify \
  -f /backups/pre_unify_$(date +%F).sql

# Apply migrations against sandbox
DATABASE_URL=$(printf 'postgresql+asyncpg://%s:%s@127.0.0.1:5432/test_unify' "$POSTGRES_USER" "$POSTGRES_PASSWORD")
DATABASE_URL="$DATABASE_URL"
  alembic -c alembic.ini upgrade head

# Inspect structures
psql -h 127.0.0.1 -U "$POSTGRES_USER" -d test_unify \
  -c "\d+ users" -c "\d+ resumes" -c "\d+ search_queries"
```
Rollback: `psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /backups/pre_unify_*.sql`.

## TLS / Certbot
```bash
sudo mkdir -p /var/www/certbot /etc/letsencrypt
sudo docker run --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/www/certbot:/var/www/certbot \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d hhoffer.ru --agree-tos -m admin@hhoffer.ru -n
sudo docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```
Enable automated renew:
```bash
sudo cp ops/systemd/certbot-renew.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now certbot-renew.timer
systemctl list-timers --all | grep certbot-renew
sudo docker run --rm -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/www/certbot:/var/www/certbot certbot/certbot renew --dry-run
```

## Secrets and BasicAuth
```bash
sudo ENV_PATH=/opt/app/.env HTPASSWD_PATH=/opt/app/nginx/.htpasswd bash ops/prepare-secrets.sh
stat -c '%a %n' /opt/app/.env /opt/app/nginx/.htpasswd
curl -I https://hhoffer.ru/admin/ping               # 401
curl -I -u admin:REDACTED https://hhoffer.ru/admin/ping
```

## Resume storage & retention
- Runtime write-test: `docker compose exec web sh -lc 'touch /app/media/resumes/_probe'`.
- Install cleaner (runs daily via cron):
  ```bash
  sudo install -m 755 ops/cleanup-resumes.sh /usr/local/bin/hh-cleanup-resumes
  echo '0 3 * * * root TARGET_DIR=/opt/app/volumes/resumes /usr/local/bin/hh-cleanup-resumes' \
    | sudo tee /etc/cron.d/hh-cleanup-resumes
  ```

## Firewall (ufw)
```bash
sudo ufw default deny incoming
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```
Rollback: `sudo ufw disable`.

## Restarting components
```bash
# Web only
docker compose -f docker-compose.prod.yml restart web
# Bot only
docker compose -f docker-compose.prod.yml restart bot
# Full stack
docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml up -d
```

## Rollback to previous image
```bash
ssh prod 'cd /opt/app/hh-bot && sed -i.bak "s/:latest/:<PREV_SHA>/" docker-compose.prod.yml'
ssh prod 'cd /opt/app/hh-bot && docker compose -f docker-compose.prod.yml up -d'
ssh prod 'cd /opt/app/hh-bot && BASE_URL=https://hhoffer.ru bash ops/smoke.sh'
```

## Rotate Telegram bot token
```bash
ssh prod 'sudo vim /opt/app/.env'  # update TELEGRAM_BOT_TOKEN
ssh prod 'cd /opt/app/hh-bot && docker compose restart bot'
ssh prod 'curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"'
```

## Backup / restore PostgreSQL
```bash
# Backup
PGPASSWORD="$POSTGRES_PASSWORD" docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > /backups/$(date +%F).sql

# Restore into new database
PGPASSWORD="$POSTGRES_PASSWORD" docker compose -f docker-compose.prod.yml exec -T db \
  psql -U "$POSTGRES_USER" "$POSTGRES_DB" < /backups/2025-09-24.sql
```

## Incident: bot cannot reach dependencies
1. `docker compose logs bot --tail=200` (watch for `Dependencies not ready`).
2. `docker compose exec db pg_isready`.
3. If migrations pending: `docker compose exec web alembic upgrade head`.
4. `docker compose restart bot`.

## Incident: `/health` degraded
1. `docker compose logs web --tail=200`.
2. Redis: `docker compose restart cache`.
3. Postgres: `docker compose restart db && docker compose exec db pg_isready`.
4. Re-run `ops/smoke.sh`.

## Smoke & failure drill
```bash
bash ops/smoke.sh
# simulate DB outage
docker compose stop db && sleep 3
curl -s -o /dev/null -w '%{http_code}' https://hhoffer.ru/health  # expect 503
docker compose start db && sleep 5
bash ops/smoke.sh
```
