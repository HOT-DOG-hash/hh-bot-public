param(
  [ValidateSet('http','https')] [string]$Mode = 'http'
)
$ErrorActionPreference = 'Stop'
Write-Host "== switch nginx to $Mode ==" -ForegroundColor Cyan

$src = Join-Path .\nginx ("nginx.$Mode.conf")
$dst = Join-Path .\nginx "nginx.conf"
if (-not (Test-Path $src)) { throw "Нет файла: $src" }

Get-Content $src -Raw | Set-Content $dst -Encoding utf8NoBOM
Write-Host "Обновил: $dst ← $src" -ForegroundColor Green

docker compose up -d --no-deps --force-recreate nginx | Out-Host

# ждём health до 60 сек
$max=120
for($i=0;$i -lt $max;$i++){
  $cid = docker compose ps -q nginx
  if(-not $cid){ Start-Sleep -Milliseconds 500; continue }
  $health = docker inspect $cid --format '{{.State.Health.Status}}' 2>$null
  if($health -eq 'healthy'){ break }
  Start-Sleep -Milliseconds 500
}
$health = docker inspect (docker compose ps -q nginx) --format '{{.State.Health.Status}}' 2>$null
Write-Host "nginx health: $health"
if($health -ne 'healthy'){
  Write-Host "`n--- nginx logs ---" -ForegroundColor DarkGray
  docker compose logs --tail=120 nginx | Out-Host
  throw "nginx не вышел в healthy"
}
