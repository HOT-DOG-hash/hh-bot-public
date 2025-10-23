#!/usr/bin/env bash
set -euo pipefail
PORT=$(python3 - <<'PYTHON'
import socket
for port in range(54329, 54350):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if sock.connect_ex(('127.0.0.1', port)) != 0:
            print(port)
            break
else:
    raise SystemExit('no free port in range 54329-54349')
PYTHON
)
container="hhbot-pg-${PORT}"
docker rm -f "$container" >/dev/null 2>&1 || true
trap 'docker rm -f "$container" >/dev/null 2>&1 || true' EXIT

docker run -d \
  --name "$container" \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=hhbot_ci \
  -p "${PORT}:5432" \
  postgres:16-alpine >/dev/null

until docker exec "$container" pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done

export DATABASE_URL="postgresql+psycopg://postgres:postgres@127.0.0.1:${PORT}/hhbot_ci"

if [ -x .venv/bin/alembic ]; then
  ALEMBIC=.venv/bin/alembic
elif command -v uvx >/dev/null 2>&1; then
  ALEMBIC="uvx alembic"
else
  ALEMBIC="alembic"
fi

$ALEMBIC downgrade base
$ALEMBIC upgrade head
$ALEMBIC downgrade base
$ALEMBIC upgrade head
