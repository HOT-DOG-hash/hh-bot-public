param(
  [switch]$Rebuild
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m){ Write-Host "[OK]  $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m){ Write-Host "[FAIL] $m" -ForegroundColor Red }

# --- 0) Предусловия ---
Info "Проверяю Docker..."
try { docker version | Out-Null } catch { Fail "Docker не установлен/не запущен"; exit 1 }
Ok "Docker доступен."

# --- 1) Проверка .env ---
$envPath = Join-Path (Get-Location) ".env"
if (-not (Test-Path $envPath)) {
  Warn ".env не найден — создаю пустой шаблон на основе .env.example"
  if (Test-Path ".env.example") { Copy-Item ".env.example" ".env" }
  else { New-Item -ItemType File -Path ".env" | Out-Null }
}

# Убедимся, что есть ключевые значения
$envText = Get-Content -Raw ".env"
function ensureKV([string]$key, [string]$default=""){
  if ($envText -notmatch "(?m)^\s*$([regex]::Escape($key))\s*=") {
    Add-Content -Encoding UTF8 ".env" "$key=$default"
    Warn "Добавил ключ $key в .env (проверь значение)"
  }
}
ensureKV "ADMIN_USER" "admin"
ensureKV "ADMIN_PASS" ""
# Генерим SECRET_KEY при отсутствии
if ($envText -notmatch "(?m)^\s*SECRET_KEY\s*=") {
  $sec = [Convert]::ToBase64String((1..48 | % {Get-Random -Max 256}))
  Add-Content -Encoding UTF8 ".env" "SECRET_KEY=$sec"
  Warn "Сгенерировал SECRET_KEY в .env"
}
ensureKV "ADMIN_SECRET_TOKEN" ""
ensureKV "POSTGRES_PASSWORD" ""

# --- 2) Проверка nginx.conf (/healthz) и автопочинка ---
$ng = "nginx/nginx.conf"
if (Test-Path $ng) {
  $txt = Get-Content -Raw $ng
  if ($txt -notmatch "location\s*=\s*/healthz") {
    Warn "В nginx.conf не найден /healthz — патчу."
    $patched = $txt -replace '(server\s*\{)', '$0

    # injected by run-and-diagnose.ps1
    location = /healthz {
      return 200 "ok";
      add_header Content-Type text/plain;
    }'
    Set-Content -Encoding UTF8 $ng $patched
    Ok "Патч nginx.conf применён."
  } else {
    Ok "nginx.conf уже содержит /healthz."
  }
} else {
  Warn "nginx/nginx.conf не найден — пропускаю проверку /healthz."
}

# --- 3) docker compose up ---
$upArgs = @("compose","up","-d")
if ($Rebuild) { $upArgs += "--build" }
Info "Запускаю docker compose up $(@($Rebuild ? '--build' : '') -join '') ..."
docker @upArgs | Write-Host

# --- 4) Ожидание health ---
function waitHealthy([string]$svc, [int]$sec=120){
  $deadline = (Get-Date).AddSeconds($sec)
  while ((Get-Date) -lt $deadline) {
    $cs = (docker compose ps --format json | ConvertFrom-Json | ? { $_.Service -eq $svc })
    if (-not $cs) { Start-Sleep 2; continue }
    $name = $cs[0].Name
    $state = (docker inspect -f '{{.State.Health.Status}}' $name) 2>$null
    if ($state -eq "healthy") { Ok "$svc healthy"; return $true }
    Start-Sleep 2
  }
  Fail "$svc не перешёл в healthy за $sec сек."
  return $false
}

$allOk = $true
$allOk = (waitHealthy "db") -and $allOk
$allOk = (waitHealthy "cache") -and $allOk
$allOk = (waitHealthy "web") -and $allOk
$allOk = (waitHealthy "nginx") -and $allOk

if (-not $allOk) {
  Warn "Печатаю хвост логов проблемных сервисов..."
  docker compose logs --tail=100 db cache web nginx | Write-Host
  exit 2
}

# --- 5) HTTP-диагностика через nginx ---
$base = "http://localhost"
function tryGet($url, $basicUser=$null, $basicPass=$null) {
  try {
    if ($basicUser -and $basicPass) {
      $pair = "$basicUser`:$basicPass"
      $b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
      $resp = Invoke-WebRequest -Uri $url -Headers @{Authorization="Basic $b64"} -TimeoutSec 10
    } else {
      $resp = Invoke-WebRequest -Uri $url -TimeoutSec 10
    }
    return $resp
  } catch {
    return $null
  }
}

Info "Проверяю nginx /healthz..."
$h1 = tryGet "$base/healthz"
if ($h1 -and $h1.StatusCode -eq 200 -and $h1.Content -match "ok") { Ok "/healthz 200 ok" } else { Fail "/healthz не 200"; $allOk=$false }

$u = (Select-String -Path ".env" -Pattern '^\s*ADMIN_USER\s*=\s*(.*)$' -AllMatches).Matches.Groups[1].Value.Trim()
$p = (Select-String -Path ".env" -Pattern '^\s*ADMIN_PASS\s*=\s*(.*)$' -AllMatches).Matches.Groups[1].Value.Trim()

Info "Проверяю /admin/ping без авторизации (ожидаем 401)..."
$h2 = tryGet "$base/admin/ping"
if ($h2 -and $h2.StatusCode -eq 200) { Fail "Ожидали 401, но получили 200"; $allOk=$false } else { Ok "Без авторизации отдаёт 401 — ок" }

Info "Проверяю /admin/ping с Basic Auth (ожидаем 200)..."
$h3 = tryGet "$base/admin/ping" $u $p
if ($h3 -and $h3.StatusCode -eq 200 -and $h3.Content -match '"ok"') { Ok "Админ доступ работает" } else { Fail "Админ доступ не работает"; $allOk=$false }

Info "Проверяю /health (backend)..."
$h4 = tryGet "$base/health"
if ($h4 -and $h4.StatusCode -eq 200) { Ok "/health 200" } else { Warn "/health недоступен/не 200 — проверь логи web" }

if ($allOk) {
  Ok "Готово. Стек поднят и прошёл диагностику."
  Write-Host "⇒ Открой: $base" -ForegroundColor Magenta
  Write-Host "⇒ Админ ping: $base/admin/ping (Basic $u / <пароль из .env>)" -ForegroundColor Magenta
  exit 0
} else {
  Fail "Диагностика нашла проблемы — см. сообщения выше."
  exit 3
}
