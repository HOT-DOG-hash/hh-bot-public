#!/usr/bin/env bash
set -euo pipefail
container="hhbot-pg"
docker rm -f "" >/dev/null 2>&1 || true
docker run -d --name "" -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=hhbot_ci -p 54329:5432 postgres:16-alpine >/dev/null
trap 'docker rm -f "" >/dev/null 2>&1 || true' EXIT
until docker exec "" pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done
export DATABASE_URL="postgresql+psycopg://postgres:postgres@127.0.0.1:54329/hhbot_ci"
if command -v uvx >/dev/null 2>&1; then
  ALEMBIC="uvx alembic"
else
  ALEMBIC="alembic"
fi
 downgrade base
 upgrade head
