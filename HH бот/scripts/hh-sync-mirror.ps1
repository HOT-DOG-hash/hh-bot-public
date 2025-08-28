<# ======================================================================
  HH BOT — MIRROR SYNC TO GITHUB
  Обновляет GitHub-репо из локального источника "как зеркало":
  пушит ВСЕ ветки/теги/refs, удаляет отсутствующие в источнике.

  Примеры:
    # из корня проекта (рабочая копия)
    & ".\HH бот\scripts\hh-sync-mirror.ps1"

    # явные параметры
    & ".\HH бот\scripts\hh-sync-mirror.ps1" `
      -Src  "C:\git-public\hh-bot-public" `
      -Dest "https://github.com/HOT-DOG-hash/hh-bot-public.git"

    # с токеном (или выставь $env:GITHUB_TOKEN):
    & ".\HH бот\scripts\hh-sync-mirror.ps1" -Token "<ghp_xxx>"

    # автоматом закоммитить ВСЁ перед зеркальным пушем (осознанно!)
    & ".\HH бот\scripts\hh-sync-mirror.ps1" -CommitAll `
      -CommitMessage "chore: mirror sync"

  Требования: установленный Git (git --version)
====================================================================== #>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
  # Источник: путь к локальному git-репозиторию (рабочая копия или bare)
  [string]$Src = (Get-Location).Path,

  # Назначение: HTTPS-URL GitHub-репозитория
  [string]$Dest = "https://github.com/HOT-DOG-hash/hh-bot-public.git",

  # GitHub Personal Access Token (если не задан, возьмём из $env:GITHUB_TOKEN)
  [string]$Token,

  # Опционально: закоммитить все изменения перед синком (ОСТОРОЖНО!)
  [switch]$CommitAll,

  # Сообщение коммита для -CommitAll
  [string]$CommitMessage = "chore: mirror sync",

  # Тихий режим (меньше болтовни)
  [switch]$Quiet
)

$ErrorActionPreference = "Stop"

function Info($msg) { if (-not $Quiet) { Write-Host $msg } }
function Fail($msg) { Write-Error $msg; exit 1 }

# --- 0) Предпроверки ----------------------------------------------------
try { git --version | Out-Null } catch { Fail "Git не найден в PATH. Установи Git и перезапусти PowerShell." }

if (-not (Test-Path $Src)) { Fail "Путь '$Src' не существует." }

# Проверяем, что это git-репозиторий (рабочая копия или bare)
$IsWorkingCopy = Test-Path (Join-Path $Src ".git")
$IsBare = $false
if (-not $IsWorkingCopy) {
  $hasObjects = Test-Path (Join-Path $Src "objects")
  $hasRefs    = Test-Path (Join-Path $Src "refs")
  $hasHead    = Test-Path (Join-Path $Src "HEAD")
  if ($hasObjects -and $hasRefs -and $hasHead) { $IsBare = $true }
}

if (-not ($IsWorkingCopy -or $IsBare)) {
  Fail "Папка '$Src' не выглядит как git-репозиторий (ни .git, ни bare-структура)."
}

if ($Dest -notmatch '^https://github\.com/.+?/.+?\.git$') {
  Fail "Ожидается HTTPS-URL GitHub, например: https://github.com/OWNER/REPO.git"
}

# --- 1) Неожиданные незакоммиченные изменения --------------------------
if ($IsWorkingCopy) {
  Push-Location $Src
  try {
    $status = git status --porcelain
    if ($status) {
      if ($CommitAll) {
        Info "Обнаружены незакоммиченные изменения — выполняю -CommitAll..."
        git add -A | Out-Null
        # коммитим, только если есть staged изменения
        if ((git diff --cached --name-only)) {
          git commit -m $CommitMessage | Out-Null
          Info "Создан коммит: $CommitMessage"
        } else {
          Info "Staged изменений нет — коммит пропущен."
        }
      } else {
        Write-Warning "Есть незакоммиченные изменения. Они НЕ попадут в зеркальный пуш!"
        Write-Warning "Либо закоммить вручную, либо перезапусти с -CommitAll."
      }
    }
  } finally { Pop-Location }
}

# --- 2) Готовим dest + токен -------------------------------------------
$EffectiveDest = $Dest
if ([string]::IsNullOrWhiteSpace($Token)) { $Token = $env:GITHUB_TOKEN }
if ($Token) {
  $EffectiveDest = $Dest -replace '^https://', ("https://{0}@" -f $Token)
  Info "Аутентификация через GitHub token."
} else {
  Info "Токен не задан. Git может запросить логин/пароль при пуше."
}

# --- 3) Mirror-клон во временную папку ----------------------------------
$tmp = Join-Path $env:TEMP ("hh-sync-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null
$mirrorPath = Join-Path $tmp "src.git"

Info "Клонирую mirror во временную папку: $mirrorPath"
if ($PSCmdlet.ShouldProcess("git clone --mirror --no-local", "clone to $mirrorPath")) {
  git clone --mirror --no-local $Src $mirrorPath | Out-Null
}

# --- 4) Обновляем ссылки и пушим как зеркало ---------------------------
Push-Location $mirrorPath
try {
  Info "Обновляю ссылки (fetch --all --prune)..."
  if ($PSCmdlet.ShouldProcess("git fetch --all --prune", "update refs")) {
    git fetch --all --prune | Out-Null
  }

  # LFS (если установлен/нужен)
  try {
    git lfs version | Out-Null
    Info "Git LFS обнаружен — подтягиваю объекты..."
    if ($PSCmdlet.ShouldProcess("git lfs fetch --all", "fetch lfs")) {
      git lfs fetch --all | Out-Null
    }
  } catch { }

  Info "Настраиваю удалённый mirror..."
  if ($PSCmdlet.ShouldProcess("git remote add mirror", "set remote")) {
    git remote remove mirror 2>$null | Out-Null
    git remote add mirror $EffectiveDest
  }

  # (необязательная) сверка SHA main (если существует)
  try {
    $localMain  = (git for-each-ref --format="%(objectname)" refs/heads/main)
    if ($localMain) {
      $remoteMain = (git ls-remote $EffectiveDest main).Split("`t")[0]
      if ($remoteMain) { Info "Сверка main: локально $localMain | удалённо $remoteMain" }
    }
  } catch { }

  Info "Пушу зеркало (branches, tags, refs) с prune..."
  $pushArgs = @("push","--prune","mirror","--mirror")
  if ($PSCmdlet.ShouldProcess("git push --mirror --prune", ($pushArgs -join ' '))) {
    git @pushArgs
  }

  Info "ЗЕРКАЛО ОБНОВЛЕНО ✅"
}
finally {
  Pop-Location
  try { Remove-Item -Recurse -Force $tmp } catch { Write-Warning "Не удалось удалить временную папку '$tmp'. Удалите вручную." }
}
