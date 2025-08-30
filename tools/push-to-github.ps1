param(
  [string]$RepoPath = ".",
  [string]$Message,
  [string]$Remote = "origin",
  [string]$Branch,
  [string]$NewRepoUrl,          # задай, если origin ещё не настроен (например: git@github.com:USER/hh-bot-public.git)
  [switch]$PushTags,            # добавь этот флаг, если хочешь запушить теги
  [switch]$CreateUpstream       # назначить upstream на origin/Branch при первом пуше
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Exec($cmd, [switch]$IgnoreError) {
  try {
    & $cmd 2>&1 | ForEach-Object { $_ }
  } catch {
    if (!$IgnoreError) { throw }
  }
}

# 0) Проверка git
try {
  Exec { git --version } | Out-Null
} catch {
  throw "Git не найден. Установи Git и перезапусти PowerShell."
}

# 1) Переходим в репозиторий
$full = Resolve-Path -Path $RepoPath
Set-Location $full
Write-Host "→ Репозиторий: $full" -ForegroundColor Cyan

# 2) Если это ещё не git-репозиторий — инициализируем
if (-not (Test-Path ".git")) {
  Write-Host "→ .git не найден — инициализирую репозиторий..." -ForegroundColor Yellow
  Exec { git init }
  if (-not $Branch) { $Branch = "main" }
  Exec { git checkout -B $Branch }
}

# 3) Определяем текущую ветку
if (-not $Branch) {
  try {
    $Branch = (Exec { git rev-parse --abbrev-ref HEAD }).Trim()
  } catch {
    $Branch = "main"
    Exec { git checkout -B $Branch }
  }
}
Write-Host "→ Ветка: $Branch" -ForegroundColor Cyan

# 4) Настраиваем удалённый репозиторий (origin)
$hasOrigin = $false
try {
  $originUrl = (Exec { git remote get-url $Remote })
  if ($originUrl) { $hasOrigin = $true }
} catch { $hasOrigin = $false }

if (-not $hasOrigin) {
  if (-not $NewRepoUrl) {
    Write-Host "⚠️  У origin нет URL. Передай -NewRepoUrl (например: git@github.com:USER/hh-bot-public.git) или добавь вручную: git remote add origin <url>" -ForegroundColor Yellow
  } else {
    Write-Host "→ Добавляю remote '$Remote' → $NewRepoUrl" -ForegroundColor Cyan
    Exec { git remote add $Remote $NewRepoUrl }
  }
} else {
  Write-Host "→ Remote '$Remote' = $originUrl" -ForegroundColor DarkGray
}

# 5) Есть ли upstream?
$hasUpstream = $false
try {
  # ВАЖНО: @ {u} в кавычках, иначе PowerShell думает, что это хэш-таблица
  $up = (Exec { git rev-parse --abbrev-ref --symbolic-full-name '@{u}' })
  if ($LASTEXITCODE -eq 0 -and $up) { $hasUpstream = $true }
} catch { $hasUpstream = $false }

if ($hasUpstream) {
  Write-Host "→ Обновляю локальную ветку (git pull --rebase --autostash)..." -ForegroundColor DarkGray
  Exec { git pull --rebase --autostash } -IgnoreError
} else {
  Exec { git fetch $Remote } -IgnoreError
}

# 6) Коммитим изменения (только если есть diff)
$changes = (Exec { git status --porcelain })
if ($changes) {
  Write-Host "→ Есть изменения — добавляю и коммичу..." -ForegroundColor Cyan
  Exec { git add -A }
  if (-not $Message) {
    $Message = "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
  }
  Exec { git commit -m $Message }
} else {
  Write-Host "→ Нет изменений для коммита." -ForegroundColor DarkGray
}

# 7) Пуш
if (-not $hasUpstream -and $CreateUpstream) {
  Write-Host "→ Назначаю upstream и пушу: $Remote/$Branch" -ForegroundColor Cyan
  Exec { git push -u $Remote $Branch }
} else {
  Write-Host "→ Пушу в $Remote $Branch" -ForegroundColor Cyan
  Exec { git push $Remote $Branch }
}

# 8) Теги (опционально)
if ($PushTags) {
  Write-Host "→ Пушу теги" -ForegroundColor Cyan
  Exec { git push --tags }
}

Write-Host "✓ Готово." -ForegroundColor Green
