#!/usr/bin/env bash
set -euo pipefail

# Допущение: запускается с правами root на хосте prod.
ENV_PATH=${ENV_PATH:-/opt/app/.env}
HTPASSWD_PATH=${HTPASSWD_PATH:-/opt/app/nginx/.htpasswd}
USER_NAME=${ADMIN_USER:-admin}

umask 077
mkdir -p "$(dirname "$ENV_PATH")"
mkdir -p "$(dirname "$HTPASSWD_PATH")"

touch "$ENV_PATH"
python - <<'PY'
import os
import secrets
from pathlib import Path

env_path = Path(os.environ['ENV_PATH'])
existing = {line.split('=', 1)[0]: line.rstrip('\n') for line in env_path.read_text().splitlines() if '=' in line}

def ensure(key: str, factory):
    if key not in existing:
        value = factory()
        existing[key] = f"{key}={value}"

ensure('SECRET_KEY', lambda: secrets.token_urlsafe(32))
ensure('ADMIN_USER', lambda: os.environ.get('USER_NAME', 'admin'))
ensure('ADMIN_PASS', lambda: secrets.token_urlsafe(24))

env_path.write_text('\n'.join(sorted(existing.values())) + '\n')
PY

chmod 600 "$ENV_PATH"

ADMIN_PASS=$(grep '^ADMIN_PASS=' "$ENV_PATH" | tail -1 | cut -d= -f2-)
umask 077
htpasswd -cbB "$HTPASSWD_PATH" "$USER_NAME" "$ADMIN_PASS" >/dev/null
chmod 600 "$HTPASSWD_PATH"

echo "[prepare] secrets updated at $ENV_PATH"
