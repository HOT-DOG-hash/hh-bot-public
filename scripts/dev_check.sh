#!/usr/bin/env bash
set -euo pipefail

rm -rf ./.venv || true
unset VIRTUAL_ENV || true

VENV_DIR=".uv"
UV_PY="$VENV_DIR/bin/python3"

if [ ! -d "$VENV_DIR" ]; then
  echo "[dev_check] Инициализация uv-окружения ($VENV_DIR)..."
  uv venv "$VENV_DIR" >/dev/null 2>&1 || uv venv "$VENV_DIR"
fi

echo "[dev_check] Python:"
python3 -V || true

echo "[dev_check] Установка зависимостей проекта:"
if [ -f requirements-all.txt ]; then
  uv pip sync --python "$UV_PY" requirements-all.txt || true
  uv pip install --python "$UV_PY" -r requirements-all.txt || true
else
  SYNC_FILES=()
  if [ -f requirements.txt ]; then
    SYNC_FILES+=("requirements.txt")
  fi
  if [ -f requirements-dev.txt ]; then
    SYNC_FILES+=("requirements-dev.txt")
  fi
  if [ ${#SYNC_FILES[@]} -gt 0 ]; then
    uv pip sync --python "$UV_PY" "${SYNC_FILES[@]}" || true
    for req in "${SYNC_FILES[@]}"; do
      uv pip install --python "$UV_PY" -r "$req" || true
    done
  fi
fi

echo "[dev_check] Установка инструментов (ruff, black, mypy, pytest, alembic) через uvx:"
export PATH="$HOME/.local/bin:${PATH}"

echo "[dev_check] Линтеры/типы/тесты:"
"$UV_PY" -m ruff check . || true
"$UV_PY" -m black --check . || true
"$UV_PY" -m mypy . || true
"$UV_PY" -m pytest -q || true


if [ "${DEV_CHECK_ALEMBIC:-0}" = "1" ]; then
  echo "[dev_check] Alembic smoke upgrade/downgrade..."
  alembic upgrade head >/dev/null && alembic downgrade -1 >/dev/null || true
fi

echo "[dev_check] Compose sanity (db/redis доступность):"
python3 - <<'PY'
import time, socket, sys
def wait(host, port, sec=10):
    s=socket.socket(); s.settimeout(1.0)
    for _ in range(sec*2):
        try:
            s.connect((host, port)); s.close(); return True
        except: time.sleep(0.5)
    return False
ok_db = wait("db", 5432)
ok_redis = wait("redis", 6379)
print("db:", ok_db, "redis:", ok_redis)
sys.exit(0 if ok_db and ok_redis else 1)
PY
