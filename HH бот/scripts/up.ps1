<# 
  Сборка и запуск стека в фоне + ожидание readiness.
  Запуск: powershell -ExecutionPolicy Bypass -File .\scripts\up.ps1
#>
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new()
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RepoRoot

./scripts/setup.ps1

Write-Host ">> docker compose up -d --build"
Invoke-Expression "$env:COMPOSE_BIN up -d --build"

# Ждём readiness /health и liveness nginx /healthz
./scripts/smoke.ps1 -Wait