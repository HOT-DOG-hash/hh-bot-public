param(
  [switch]$Rebuild
)

$ErrorActionPreference = "Stop"

function Die($msg) { Write-Host "[FATAL] $msg" -ForegroundColor Red; exit 1 }

Write-Host "[INFO] Проверяю Docker daemon..." -ForegroundColor Cyan
try {
  $null = docker info | Out-Null
} catch {
  Write-Host "[ERR] Docker недоступен: $($_.Exception.Message)" -ForegroundColor Red
  Write-Host "  → Запусти Docker Desktop и дождись, пока 'docker info' заработает." -ForegroundColor Yellow
  exit 1
}

Write-Host "[OK] Docker доступен." -ForegroundColor Green

if ($Rebuild) {
  Write-Host "[INFO] docker compose up -d --build" -ForegroundColor Cyan
  docker compose up -d --build
} else {
  Write-Host "[INFO] docker compose up -d" -ForegroundColor Cyan
  docker compose up -d
}

Write-Host "[INFO] Жду статусы..." -ForegroundColor Cyan
$deadline = (Get-Date).AddMinutes(2)
$services = @("db","cache","web","nginx")

function Status($s) {
  docker compose ps --format json | ConvertFrom-Json | Where-Object { $_.Service -eq $s }
}

foreach ($s in $services) {
  while ($true) {
    $st = Status $s
    if (-not $st) { Start-Sleep 1; if ((Get-Date) -gt $deadline) { Die "Нет контейнера $s" } ; continue }
    if ($st.State -match "healthy|running") { Write-Host "[OK] $s $($st.State)" -ForegroundColor Green; break }
    if ((Get-Date) -gt $deadline) { Write-Host "[WARN] $s статус: $($st.State)" -ForegroundColor Yellow; break }
    Start-Sleep 2
  }
}

Write-Host "[INFO] Пробую локовые пробы nginx..." -ForegroundColor Cyan
try {
  $c1 = curl -s -o $null -w '%{http_code}' http://localhost/healthz
  $c2 = curl -s -o $null -w '%{http_code}' http://localhost/health
  Write-Host "  /healthz → $c1, /health → $c2"
} catch { Write-Host "[ERR] curl localhost:80 не отвечает" -ForegroundColor Red }

Write-Host "[INFO] Проверяю админ-пинг..." -ForegroundColor Cyan
$User = $env:ADMIN_USER; if (-not $User) { $User = "admin" }
$Pass = $env:ADMIN_PASS; if (-not $Pass) { $Pass = "pass" }

try {
  $a = curl -s -o $null -w '%{http_code}' -u "$User`:$Pass" http://localhost/admin/ping
  Write-Host "  /admin/ping → $a"
} catch { Write-Host "[ERR] curl /admin/ping упал" -ForegroundColor Red }

Write-Host "[INFO] Переменные в web:" -ForegroundColor Cyan
docker compose exec web sh -lc 'env | grep -E "^(ADMIN_USER|ADMIN_PASS|WEB_PORT)="' || Write-Host "  (нет доступа к web)" -ForegroundColor Yellow

Write-Host "[DONE] Диагностика завершена." -ForegroundColor Green
