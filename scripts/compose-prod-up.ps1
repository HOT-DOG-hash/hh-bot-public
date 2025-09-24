Param(
  [switch]$LocalBuild  # -LocalBuild => использовать override для локальной сборки
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Проверка .env
if (-not (Test-Path ".env")) { throw ".env not found at $(Get-Location)" }

# Быстрая проверка .htpasswd
if (-not (Test-Path "nginx\.htpasswd")) { throw "nginx\.htpasswd not found" }
$line = Get-Content nginx\.htpasswd -TotalCount 1
if ($line -notmatch '^admin:\$apr1\$') {
  Write-Warning "nginx\.htpasswd не APR1. Рекомендуется заменить (openssl passwd -apr1)."
}

# Сборка локальных образов (если флаг)
$files = @("docker-compose.prod.yml")
if ($LocalBuild) { $files += "docker-compose.prod.local.yml" }

# Поднятие
docker compose -f $files up -d nginx

# Проверки
docker compose -f $files exec nginx nginx -t
curl -s -o NUL -w "HTTP=%{http_code}`n" http://127.0.0.1/healthz
Write-Host "OK. Проверь https://hhoffer.ru/healthz и /admin/ (401 без логина)."
