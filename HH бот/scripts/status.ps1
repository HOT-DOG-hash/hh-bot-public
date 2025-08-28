<# 
  Состояние контейнеров + краткие логи web.
  Запуск: powershell -ExecutionPolicy Bypass -File .\scripts\status.ps1
#>
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RepoRoot

docker compose ps
Write-Host "`n--- web last 50 lines ---`n"
docker compose logs --tail=50 web
