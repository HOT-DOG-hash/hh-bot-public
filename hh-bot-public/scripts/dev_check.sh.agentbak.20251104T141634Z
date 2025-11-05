#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# Разрешение интерпретатора venv (Windows/Unix)
if [ -x ".venv/bin/python" ]; then
  VENV_PY=".venv/bin/python"
elif [ -x ".venv/Scripts/python.exe" ]; then
  VENV_PY=".venv/Scripts/python.exe"
else
  uv python install 3.12
  uv venv -p 3.12 .venv
  if [ -x ".venv/bin/python" ]; then
    VENV_PY=".venv/bin/python"
  else
    VENV_PY=".venv/Scripts/python.exe"
  fi
fi

echo ">>> [deps] sync dev deps"
uv pip install --python "$VENV_PY" -r requirements-dev.txt
uv pip install --python "$VENV_PY" aiosqlite

# Устанавливаем fallback на локальную SQLite, если DATABASE_URL не задан
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./tmp_smoke.db}"

# Базовые ENV по умолчанию для smoke-сценариев
export ADMIN_USER="${ADMIN_USER:-admin}"
export ADMIN_PASS="${ADMIN_PASS:-secret}"
export BASE_URL="${BASE_URL:-http://localhost:8000}"
export SECRET_KEY="${SECRET_KEY:-dev-secret}"
export ADMIN_SECRET_TOKEN="${ADMIN_SECRET_TOKEN:-dev-admin-token}"
export YOOMONEY_WEBHOOK_SECRET="${YOOMONEY_WEBHOOK_SECRET:-dev-webhook-secret}"
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-dev-telegram-token}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

echo ">>> [lint] ruff"
uv run --python "$VENV_PY" ruff check .

echo ">>> [types] mypy"
uv run --python "$VENV_PY" mypy backend front_bot

if [ "${SKIP_DB_SMOKE:-0}" = "1" ]; then
  echo ">>> [db] smoke skipped by SKIP_DB_SMOKE=1"
else
  echo ">>> [db] alembic smoke on $DATABASE_URL"
  uv run --python "$VENV_PY" alembic downgrade base
  uv run --python "$VENV_PY" alembic upgrade head
fi

echo ">>> [tests] sqlite-only"
uv run --python "$VENV_PY" pytest -q -m "not pg"

echo ">>> OK"
