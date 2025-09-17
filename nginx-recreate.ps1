$ErrorActionPreference = 'Continue'
Write-Host "== nginx: recreate ==" -ForegroundColor Cyan

docker compose rm -sf nginx | Out-Host
docker compose up -d nginx   | Out-Host

"`nСтатус:" | Out-Host
docker compose ps | Out-Host

"`nЛоги (последние 80 строк):" | Out-Host
docker compose logs --tail=80 nginx | Out-Host
