param(
  [string]$RepoPath = ".",
  [switch]$TestPush
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ok($msg)    { Write-Host "[OK] $msg" -ForegroundColor Green }
function Warn($msg)  { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Fail($msg)  { Write-Host "[FAIL] $msg" -ForegroundColor Red }

function Exec($cmd) {
  & $cmd 2>&1
}

# 1. Проверка git
try {
  $gitver = Exec { git --version }
  Ok "Git найден: $gitver"
} catch {
  Fail "Git не найден. Установи Git."
  exit 1
}

# 2. Переход в репо
$full = Resolve-Path -Path $RepoPath
Set-Location $full
Ok "Репозиторий: $full"

# 3. Проверка .git
if (-not (Test-Path ".git")) {
  Fail "Это не git-репозиторий."
  exit 1
}

# 4. Текущая ветка
$branch = (Exec { git rev-parse --abbrev-ref HEAD }).Trim()
Ok "Текущая ветка: $branch"

# 5. Remote
try {
  $originUrl = (Exec { git remote get-url origin }).Trim()
  Ok "origin = $originUrl"
} catch {
  Warn "Remote 'origin' не настроен"
}

# 6. Upstream
try {
  $up = (Exec { git rev-parse --abbrev-ref --symbolic-full-name '@{u}' }) -join "`n"
  if ($LASTEXITCODE -eq 0 -and $up) {
    Ok "Upstream для ${branch}: $up"
  } else {
    Warn "Upstream не настроен для ${branch}"
  }
} catch {
  Warn "Upstream не найден"
}

# 7. Статус изменений
$changes = Exec { git status --porcelain }
if ($changes) {
  Warn "Есть незафиксированные изменения:"
  $changes | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
} else {
  Ok "Нет локальных изменений"
}

# 8. Проверка .gitattributes
if (Test-Path ".gitattributes") {
  $lines = Get-Content ".gitattributes"
  foreach ($l in $lines) {
    if ($l -match "^\s") {
      Warn ".gitattributes содержит строки с пробелами в начале → может быть причиной ошибки push"
      break
    }
  }
}

# 9. Тестовый push (если включен флаг)
if ($TestPush) {
  Write-Host "`n[TEST PUSH]" -ForegroundColor Cyan
  Exec { git push --dry-run origin $branch } | ForEach-Object {
    Write-Host $_
    if ($_ -match "secret" -or $_ -match "GH013") {
      Fail "GitHub отклонил push: найдены секреты или правила безопасности"
    }
    if ($_ -match "not a valid attribute name") {
      Fail "Ошибка .gitattributes: некорректные строки"
    }
  }
}

Ok "Диагностика завершена."
