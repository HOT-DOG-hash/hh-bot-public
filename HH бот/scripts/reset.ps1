<# 
  Полная остановка + удаление volume'ов и orphans (осторожно: сотрёт БД в volume).
  Запуск: powershell -ExecutionPolicy Bypass -File .\scripts\reset.ps1
#>
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RepoRoot

docker compose down -v --remove-orphans
