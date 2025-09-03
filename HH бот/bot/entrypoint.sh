#!/usr/bin/env bash
set -Eeuo pipefail

# 1) Логи без буферов — полезно в контейнерах
export PYTHONUNBUFFERED=1

# 2) Если .env существует внутри образа/тома — подгрузим (CRLF -> LF)
#   Это запасной вариант — обычно переменные уже приходят из compose env_file.
if [[ -f "/app/.env" ]]; then
  sed -i 's/\r$//' /app/.env
  set -a; source /app/.env; set +a
fi

# 3) PYTHONPATH по умолчанию — учитываем пробелы/кириллицу в пути
export PYTHONPATH="${PYTHONPATH:-/app:/app/HH бот}"

# 4) Флажок на случай, если код его использует
export ENABLE_TELEGRAM_BOT=1

# 5) Fail fast: без токена бота запуск бессмысленен
if [[ -z "${TELEGRAM_BOT_TOKEN:-}" && -z "${BOT_TOKEN:-}" ]]; then
  echo "[bot] ERROR: TELEGRAM_BOT_TOKEN (или BOT_TOKEN) не задан. Завершаюсь." >&2
  exit 1
fi

# 6) Проверим, что раннер существует
RUNNER_PATH="/app/HH бот/bot/runner.py"
if [[ ! -f "$RUNNER_PATH" ]]; then
  echo "[bot] ERROR: Не найден файл раннера: $RUNNER_PATH" >&2
  exit 1
fi

echo "[bot] Starting runner..."
echo "[bot] PYTHONPATH=${PYTHONPATH}"
echo "[bot] Using token: $([[ -n "${TELEGRAM_BOT_TOKEN:-}" || -n "${BOT_TOKEN:-}" ]] && echo '***SET***' || echo '***MISSING***')"
echo "[bot] Runner: $RUNNER_PATH"

# 7) Важно: exec — чтобы Python стал PID 1 и корректно ловил SIGTERM/SIGINT
exec python "$RUNNER_PATH"
