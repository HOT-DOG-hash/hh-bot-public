# tools/run-local.ps1
param(
  [string]$Host = "127.0.0.1",
  [int]$Port = 8000,
  [string]$AdminUser = "admin",
  [string]$AdminPass = "pass",
  [switch]$WithDeps,     # запустить локальные зависимости в docker (db, redis)
  [switch]$Reload        # включить --reload (осторожно на Windows)
)

$ErrorActionPreference = "Stop"

# 1) Каталог приложения (в нём лежит backend/)
$AppDir = Join-Path $PSScriptRoot "..\HH бот"
$AppDir = [IO.Path]::GetFullPath($AppDir)

if (-not (Test-Path $AppDir)) {
  throw "Не найден каталог приложения: $AppDir"
}

# 2) Переменные окружения для BasicAuth
$env:ADMIN_USER = $AdminUser
$env:ADMIN_PASS = $AdminPass

# 3) (Опционально) Локальные зависимости через docker
if ($WithDeps) {
  Write-Host "[INFO] Поднимаю локальные зависимости (Postgres/Redis)..." -ForegroundColor Cyan
  Push-Location (Join-Path $PSScriptRoot "..")
  try {
    docker compose up -d db cache | Out-Null
  } finally {
    Pop-Location
  }
  # Для /health можно указать хостовые URL’ы
  $env:DATABASE_URL = "postgresql+asyncpg://hh:hh@localhost:5432/hh"
  $env:REDIS_URL    = "redis://localhost:6379/0"
}

# 4) Запуск uvicorn
Set-Location $AppDir
$cmd = @("python","-m","uvicorn","backend.app.main:app","--host",$Host,"--port",$Port,"--log-level","debug")
if ($Reload) { $cmd += @("--reload","--reload-dir",".") }

Write-Host "[RUN] $($cmd -join ' ')" -ForegroundColor Green
& $cmd
