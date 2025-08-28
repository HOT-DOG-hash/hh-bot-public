<# 
  Быстрый рестарт только прикладных сервисов.
  Запуск: powershell -ExecutionPolicy Bypass -File .\scripts\restart.ps1
#>
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RepoRoot

docker compose restart web bot nginx
