<# ======================================================================
  HH BOT — CHECK & FIX (PowerShell)
  Запуск:
    .\scripts\hh-check.ps1
    .\scripts\hh-check.ps1 -Rebuild
    .\scripts\hh-check.ps1 -Tail
    .\scripts\hh-check.ps1 -Token "12345:AA...." -Rebuild -Tail

  Что делает:
   1) Проверяет docker compose состояние
   2) (опц.) Записывает корневой .env с TELEGRAM_BOT_TOKEN/BOT_TOKEN (UTF-8 без BOM)
   3) (опц.) Пересобирает и поднимает bot
   4) Проверяет токены внутри контейнера
   5) Интроспекция Python-модулей/хэндлеров (routers.start/…)
   6) Проверка entrypoint на BOM/CRLF в контейнере
   7) Ищет лишние .env в /bot (не должно быть)
   8) Health web/nginx, готовность БД
   9) (опц.) Тейлит логи бота
====================================================================== #>

[CmdletBinding()]
param(
  [switch]$Rebuild,
  [switch]$Tail,
  [string]$Token
)

$ErrorActionPreference = "Stop"

function Write-Section([string]$t) { Write-Host "`n== $t ==" -ForegroundColor Cyan }
function ExecBot([string]$cmd)     { docker compose exec -T bot sh -lc $cmd }
function ExecWeb([string]$cmd)     { docker compose exec -T web sh -lc $cmd }
function ExecNginx([string]$cmd)   { docker compose exec -T nginx sh -lc $cmd }
function ExecDb([string]$cmd)      { docker compose exec -T db sh -lc $cmd }

# --- 0) Подготовка: корень проекта
$repoRoot = (Resolve-Path ".").Path
if (-not (Test-Path "$repoRoot\docker-compose.yml")) {
  throw "Запускай из корня проекта: рядом должен быть docker-compose.yml"
}

# --- 1) docker compose ps
Write-Section "docker compose status"
docker compose ps

# --- 2) Если передали -Token — записываем корневой .env (для compose-подстановок)
if ($Token) {
  Write-Section "запись .env (compose) — TELEGRAM_BOT_TOKEN/BOT_TOKEN"
  $envPath = Join-Path $repoRoot ".env"
  $content = @"
TELEGRAM_BOT_TOKEN=$Token
BOT_TOKEN=$Token
"@
  # UTF-8 без BOM
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($envPath, $content, $utf8NoBom)
  Write-Host ".env обновлён: $envPath"
  Write-Host "TOKEN(head):" -NoNewline; Write-Host (" " + $Token.Substring(0,[Math]::Min(6,$Token.Length)) + "...") -ForegroundColor Yellow
}

# --- 3) (опц.) пересборка/поднятие bot
if ($Rebuild) {
  Write-Section "compose up -d --build bot"
  docker compose up -d --build bot
}

# --- 4) Подождать, пока bot не станет running/restarting не будет
Write-Section "ожидание запуска bot (до 30 сек.)"
$ok=$false
for ($i=0; $i -lt 30; $i++) {
  $st = (docker compose ps --format json | ConvertFrom-Json) | Where-Object { $_.Service -eq "bot" }
  if ($st -and $st.State -match "running") { $ok=$true; break }
  Start-Sleep -Seconds 1
}
if (-not $ok) { Write-Warning "bot ещё не running — продолжаю проверки, но некоторые шаги могут упасть" }

# --- 5) Токены внутри контейнера
Write-Section "bot: env tokens внутри контейнера"
try {
  ExecBot 'printenv | grep -E "^(BOT_TOKEN|TELEGRAM_BOT_TOKEN)=" || true'
} catch { Write-Warning $_ }

# --- 6) Интроспекция Python (версии и наличие хэндлеров)
Write-Section "bot: Python/handlers интроспекция"
try {
  ExecBot @'
python - << "PY"
import sys, importlib
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
for mod, attrs in (("routers.start", ("start","start_over","link_account","in_development")),):
    m = importlib.import_module(mod)
    print(mod, {a:getattr(m,a,None) is not None for a in attrs})
PY
'@
} catch { Write-Warning $_ }

# --- 7) entrypoint: BOM/CRLF
Write-Section "bot: entrypoint BOM/CRLF"
try {
  ExecBot 'echo -n "first-3-bytes(hex): "; od -An -t x1 -N 3 /bot/entrypoint.sh | tr -d " \n"; echo'
  ExecBot 'echo "CRLF probe (^M should be absent):"; sed -n "1,8{s/\r/<CR>/g;p}" /bot/entrypoint.sh'
} catch { Write-Warning $_ }

# --- 8) Лишние .env в /bot (быть не должно — entrypoint их отключает)
Write-Section "bot: stray .env files"
try {
  ExecBot 'find /bot -maxdepth 2 -type f -name ".env" -printf "%p\n" 2>/dev/null || true'
} catch { Write-Warning $_ }

# --- 9) web/nginx health (условно)
Write-Section "web/nginx health"
try {
  ExecWeb 'curl -fsS http://127.0.0.1:8000/health || exit 1'
} catch { Write-Warning "web health fail: $_" }

# пропускаем nginx, если его нет в compose
$services = docker compose ps --format json | ConvertFrom-Json
$hasNginx = $services | Where-Object { $_.Service -eq 'nginx' }
if ($hasNginx) {
  try { ExecNginx 'wget -qO- http://127.0.0.1/ | head -n 3' } catch { Write-Warning "nginx check fail: $_" }
} else {
  Write-Host "nginx service not present — skipping" -ForegroundColor Yellow
}

# --- 10) База данных готовность
Write-Section "db readiness"
$pgUser = $env:POSTGRES_USER; if (-not $pgUser) { $pgUser = "hh" }
$pgDb   = $env:POSTGRES_DB;   if (-not $pgDb)   { $pgDb   = "hh" }
try {
  ExecDb "pg_isready -U $pgUser -d $pgDb || exit 1"
} catch {
  Write-Warning "pg_isready fail: $_"
}

# --- 11) последние логи
Write-Section "bot: последние логи (5 мин)"
try { docker compose logs --since 5m bot } catch { Write-Warning $_ }

# --- 12) (опц.) tail
if ($Tail) {
  Write-Section "tail -f bot (Ctrl+C для выхода)"
  docker compose logs -f bot
}
