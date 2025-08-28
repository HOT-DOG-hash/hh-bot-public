<# 
  Полный чек аппа: контейнеры, токены, импорт модулей, CRLF/BOM, .env, веб-здоровье.
  Запускать из корня проекта:  .\scripts\check-all.ps1
#>

$ErrorActionPreference = "Stop"

function ExecBot([string]$cmd) {
  docker compose exec -T bot sh -lc $cmd
}

Write-Host "== docker compose status ==" -ForegroundColor Cyan
docker compose ps

Write-Host "`n== bot: env tokens ==" -ForegroundColor Cyan
ExecBot 'printenv | egrep "BOT_TOKEN|TELEGRAM_BOT_TOKEN" || true'

Write-Host "`n== bot: Python introspection (handlers, версии) ==" -ForegroundColor Cyan
ExecBot @'
python - << "PY"
import sys, importlib, inspect
print("python:", sys.version.split()[0])
try:
    import telegram
    print("python-telegram-bot:", getattr(telegram, "__version__", "unknown"))
except Exception as e:
    print("telegram import error:", e)

def safe_import(name):
    try:
        m = importlib.import_module(name)
        print(f"imported: {name} ->", getattr(m, "__file__", "n/a"))
        return m
    except Exception as e:
        print(f"import failed: {name} -> {e}")
        return None

s = safe_import("routers.start")
r = safe_import("routers.responses")

if s:
    for attr in ("start","start_over","link_account","in_development"):
        print(f"routers.start.{attr}:", hasattr(s, attr))
PY
'@

Write-Host "`n== bot: entrypoint line-endings / BOM ==" -ForegroundColor Cyan
ExecBot 'echo -n "first-3-bytes(hex): "; od -An -t x1 -N 3 /bot/entrypoint.sh | tr -d " \n"; echo'
ExecBot 'echo "CRLF check (^M should be absent):"; sed -n "1,5{s/\r/<CR>/g;p}" /bot/entrypoint.sh'

Write-Host "`n== bot: stray .env files (должно быть пусто) ==" -ForegroundColor Cyan
ExecBot 'find /bot -maxdepth 2 -type f -name ".env" -printf "%p\n" 2>/dev/null || true'

Write-Host "`n== bot: last logs ==" -ForegroundColor Cyan
docker compose logs --since 5m bot

Write-Host "`n== web/nginx health ==" -ForegroundColor Cyan
try {
  docker compose exec -T web  sh -lc 'curl -fsS http://127.0.0.1:8000/health || exit 1' | Write-Host
  docker compose exec -T nginx sh -lc 'wget -qO- http://127.0.0.1/ | head -n 3' | Write-Host
} catch {
  Write-Warning "web/nginx health check failed: $_"
}

Write-Host "`n== db: readiness ==" -ForegroundColor Cyan
# Используем дефолты из compose, подставь свои при необходимости
$pgUser = $env:POSTGRES_USER; if (-not $pgUser) { $pgUser = "hh" }
$pgDb   = $env:POSTGRES_DB;   if (-not $pgDb)   { $pgDb   = "hh" }
docker compose exec -T db sh -lc "pg_isready -U $pgUser -d $pgDb || exit 1"

Write-Host "`n== done =="
