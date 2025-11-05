# ensure-admin.ps1
param(
  [string]$User = "admin",
  [string]$Pass = "pass"
)

$ErrorActionPreference = "Stop"
$envFile = ".env"

# 1) Правим/добавляем значения в .env
if (-not (Test-Path $envFile)) { New-Item -ItemType File -Path $envFile | Out-Null }
$envText = Get-Content -Raw $envFile
$envText = if ($envText -match '(?m)^\s*ADMIN_USER\s*=') {
  ($envText -replace '(?m)^\s*ADMIN_USER\s*=.*$', "ADMIN_USER=$User")
} else { $envText.TrimEnd() + "`r`nADMIN_USER=$User`r`n" }

$envText = if ($envText -match '(?m)^\s*ADMIN_PASS\s*=') {
  ($envText -replace '(?m)^\s*ADMIN_PASS\s*=.*$', "ADMIN_PASS=$Pass")
} else { $envText.TrimEnd() + "`r`nADMIN_PASS=$Pass`r`n" }

Set-Content -Path $envFile -Value $envText -Encoding UTF8

Write-Host "[OK] .env обновлён: ADMIN_USER=$User, ADMIN_PASS set" -ForegroundColor Green

# 2) Перезапускаем только web и проверяем, что внутри видны переменные
docker compose up -d --no-deps --build web | Out-Null
Start-Sleep -Seconds 2

Write-Host "[INFO] env внутри web:" -ForegroundColor Cyan
docker compose exec web sh -lc 'env | grep "^ADMIN_"' || Write-Host "(нет ADMIN_ переменных)" -ForegroundColor Yellow

# 3) Локальный тест изнутри web
Write-Host "[TEST] web → /admin/ping" -ForegroundColor Cyan
docker compose exec web sh -lc "curl -s -o /dev/null -w '%{http_code}\n' -u $User:$Pass http://127.0.0.1:8000/admin/ping" |
  ForEach-Object {
    if ($_ -eq "200") { Write-Host "[OK] web отвечает 200" -ForegroundColor Green }
    else { Write-Host "[ERR] web отвечает HTTP $_" -ForegroundColor Red }
  }

# 4) Тест через nginx
Write-Host "[TEST] nginx → /admin/ping" -ForegroundColor Cyan
$code = (curl -s -o $null -w '%{http_code}' -u "$User`:$Pass" http://localhost/admin/ping)
if ($code -eq "200") { Write-Host "[OK] nginx проксирует 200" -ForegroundColor Green }
else { Write-Host "[ERR] nginx отвечает HTTP $code" -ForegroundColor Red }
