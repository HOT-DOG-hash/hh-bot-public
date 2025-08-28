<# 
  Хвост логов и лайв-стрим (прерывание Ctrl+C).
  Параметры:
    -Service web|bot|nginx|db|cache (по умолчанию web,bot,nginx)
  Пример:
    .\scripts\logs.ps1
    .\scripts\logs.ps1 -Service web
#>
param(
  [string[]]$Service = @("web","bot","nginx")
)
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RepoRoot

docker compose logs --tail=100 @Service
Write-Host "`n--- Follow (Ctrl+C для выхода) ---`n"
docker compose logs -f @Service
