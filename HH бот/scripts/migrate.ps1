<# 
  Применение миграций Alembic внутри контейнера web.
  Запуск: powershell -ExecutionPolicy Bypass -File .\scripts\migrate.ps1
#>
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RepoRoot

try {
  docker compose exec -T web alembic upgrade head
  Write-Host "Alembic миграции применены."
} catch {
  Write-Warning "Ошибка выполнения alembic upgrade head. Проверь наличие alembic.ini и каталога migrations в образе web."
  throw
}
