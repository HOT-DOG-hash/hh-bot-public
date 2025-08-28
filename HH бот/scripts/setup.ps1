<#
  Инициализация окружения:
  - Проверка Docker CLI и compose (v2 или legacy docker-compose)
  - Создание .env из .env.example (если отсутствует)
  - Базовая валидация файлов
  Запуск:  powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
#>

$ErrorActionPreference = 'Stop'
$PSStyle.OutputRendering = 'Host'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new()

# Переход в корень репозитория
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RepoRoot
Write-Host ">> Repo root: $RepoRoot"

function Fail($msg) {
  Write-Error $msg
  exit 1
}

# --- Поиск docker CLI ---
$DockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $DockerCmd) {
  # Иногда docker.exe не в PATH до первого запуска Docker Desktop
  Write-Warning "Docker CLI не найден в PATH."
  Write-Host "Проверь, что Docker Desktop установлен и запущен."
  Write-Host "После установки перезапусти PowerShell. Ожидается docker.exe в PATH."
  Fail "Docker не найден. Установи/запусти Docker Desktop и повтори."
}

# --- Проверка daemon'а ---
try { docker version | Out-Null } catch { Fail "Docker установлен, но daemon недоступен. Открой Docker Desktop и дождись статуса 'Running'." }

# --- Поиск compose (v2 плагин или legacy) ---
$HasComposeV2 = $false
$HasComposeLegacy = $false

try { docker compose version | Out-Null; $HasComposeV2 = $true } catch {}
if (-not $HasComposeV2) {
  $dc = Get-Command docker-compose -ErrorAction SilentlyContinue
  if ($dc) {
    try { docker-compose version | Out-Null; $HasComposeLegacy = $true } catch {}
  }
}

if (-not ($HasComposeV2 -or $HasComposeLegacy)) {
  Fail "Не найден ни 'docker compose' (v2), ни 'docker-compose' (legacy). Обнови Docker Desktop до актуальной версии."
}

# .env
if (-not (Test-Path ".\.env")) {
  if (-not (Test-Path ".\.env.example")) {
    Fail ".env и .env.example не найдены. Добавь .env.example в корень."
  }
  Copy-Item ".\.env.example" ".\.env"
  Write-Host "Создан .env из .env.example — заполни значения при необходимости."
} else {
  Write-Host ".env найден."
}

# Наличие ключевых файлов
$mustExist = @(
  ".\docker-compose.yml",
  ".\nginx\nginx.conf",
  ".\HH бот\backend\Dockerfile",
  ".\HH бот\backend\app\main.py",
  ".\HH бот\front_bot\Dockerfile",
  ".\HH бот\front_bot\requirements.txt"
)

$missing = @()
foreach ($p in $mustExist) {
  if (-not (Test-Path $p)) { $missing += $p }
}
if ($missing.Count -gt 0) {
  Write-Warning "Отсутствуют ожидаемые файлы:`n$($missing -join "`n")"
} else {
  Write-Host "Все ключевые файлы на месте."
}

# Экспорт флага для других скриптов: какой compose доступен
if ($HasComposeV2) {
  $env:COMPOSE_BIN = "docker compose"
} else {
  $env:COMPOSE_BIN = "docker-compose"
}
Write-Host "Compose: $env:COMPOSE_BIN"

Write-Host "Setup завершён."
