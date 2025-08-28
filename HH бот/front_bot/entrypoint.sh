#!/usr/bin/env sh
set -eu

# 0) Логи: заранее попробуем подготовить каталог/файл, но без фанатизма
LOG_DIR="${BOT_LOG_DIR:-/var/log/app}"
LOG_FILE="${BOT_LOG_FILE:-$LOG_DIR/bot.log}"
mkdir -p "$LOG_DIR" 2>/dev/null || true
: > "$LOG_FILE" 2>/dev/null || true

# 1) Токен: берём из любых переменных и НОРМАЛИЗУЕМ (срезаем \r\n\t и пробелы)
v="${TELEGRAM_BOT_TOKEN:-${BOT_TOKEN:-}}"
vv=$(printf %s "$v" | tr -d '\r\n\t ')

len=$(printf %s "$vv" | wc -c | tr -d ' ')
head=$(printf %s "$vv" | cut -c1-6 || true)
ok="no"
printf %s "$vv" | grep -q ":" && [ "$len" -ge 30 ] && ok="yes"
echo "ENTRYPOINT: token len=${len}, head=${head}, ok=${ok}"

# 2) Экспортируем обе переменные (жёстко), чтобы импорты/библиотеки не промазали
export TELEGRAM_BOT_TOKEN="$vv"
export BOT_TOKEN="$vv"

# 3) Обезвреживаем любые .env рядом с кодом, чтобы они НЕ перетёрли окружение
disable_env_file() {
  f="$1"
  if [ -f "$f" ]; then
    echo "ENTRYPOINT: disabling $f to avoid overriding env"
    mv -f "$f" "${f}.disabled" || true
  fi
}
disable_env_file "/bot/.env"
disable_env_file "/bot/front_bot/.env"
disable_env_file "/bot/config/.env"
if command -v find >/dev/null 2>&1; then
  for f in $(find /bot -maxdepth 2 -type f -name ".env" 2>/dev/null); do
    case "$f" in
      /bot/.env|/bot/front_bot/.env|/bot/config/.env) : ;;
      *) disable_env_file "$f" ;;
    esac
  done
fi

# 4) Пуск
exec python -u /bot/main.py
