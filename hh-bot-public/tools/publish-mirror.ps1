param(
  [string]$Remote = "origin",
  [string]$Branch = "",              # если пусто — текущая ветка
  [switch]$SkipScan,                 # не запускать scan-secrets
  [switch]$AllowRegexFindings,       # продолжать, даже если regex-скан что-то нашёл
  [switch]$NoVerify,                 # коммит без pre-commit хуков ( --no-verify )
  [switch]$DryRun                    # показать, что будет сделано
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$scannerScript = Join-Path $repoRoot 'scan-secrets.ps1'
$gitleaksConfig = Join-Path $repoRoot '.gitleaks.toml'

function Get-CurrentBranch { (git rev-parse --abbrev-ref HEAD).Trim() }

Write-Host "== publish-mirror : start ==" -ForegroundColor Cyan

# 1) Проверка секретов
if (-not $SkipScan) {
  if (-not (Test-Path $scannerScript)) {
    throw "scan-secrets script not found at $scannerScript"
  }

  Write-Host "Running scan-secrets.ps1 ..." -ForegroundColor Yellow
  pwsh -File $scannerScript
  $exit = $LASTEXITCODE
  if ($exit -ne 0 -and -not $AllowRegexFindings) {
    throw "Secret scan reported findings (exit=$exit). Fix them or re-run with -AllowRegexFindings to proceed."
  }

  $gitleaksCmd = Get-Command gitleaks -ErrorAction SilentlyContinue
  if ($gitleaksCmd) {
    $reportsDir = Join-Path $PSScriptRoot 'reports'
    if (-not (Test-Path $reportsDir)) {
      New-Item -ItemType Directory -Path $reportsDir | Out-Null
    }

    $reportFile = Join-Path $reportsDir ("gitleaks-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".json")
    $detectArgs = @(
      'detect',
      '--no-banner',
      '--redact',
      '--report-format', 'json',
      '--report-path', $reportFile,
      '--source', $repoRoot
    )
    if (Test-Path $gitleaksConfig) {
      $detectArgs += @('--config', $gitleaksConfig)
    }

    Write-Host "Running gitleaks detect ..." -ForegroundColor Yellow
    & $gitleaksCmd @detectArgs
    $gitleaksExit = $LASTEXITCODE
    if ($gitleaksExit -ne 0 -and -not $AllowRegexFindings) {
      throw "gitleaks reported findings (exit=$gitleaksExit). Resolve leaks or re-run with -AllowRegexFindings to proceed. Report: $reportFile"
    }
    if ($gitleaksExit -eq 0) {
      Write-Host "gitleaks report saved to $reportFile" -ForegroundColor DarkCyan
    }
  } else {
    Write-Host "gitleaks not found in PATH, skipping secondary scan." -ForegroundColor DarkYellow
  }
}

# 2) Гарантированно убрать из индекса секретные/локальные артефакты
# ВАЖНО: .env.example остаётся в репо
$pathsToUntrack = @(
  ".env", ".env.prod", ".env.bak", "HH бот/.env.dev",
  "nginx/htpasswd",
  "tools/reports", ".mirror.git", ".remote-mirror.git",
  "gitleaks-history.json", "trufflehog-*.json"
)
Write-Host "Ensuring sensitive paths are not tracked..." -ForegroundColor Yellow
foreach ($p in $pathsToUntrack) {
  try { git rm -r --cached -- $p 2>$null | Out-Null } catch { }
}

# 3) Обновить .gitignore (если правили)
if (Test-Path ".gitignore") { git add .gitignore | Out-Null }

# 4) Добавить все рабочие изменения (кроме игнорируемых)
git add -A

# 5) Сделать коммит (если есть изменения)
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
  Write-Host "Nothing to commit. Working tree is clean." -ForegroundColor Green
} else {
  $msg = "chore(security): clean mirror before publish"
  if ($DryRun) {
    Write-Host "`n[DRYRUN] Would commit with message:`n  $msg" -ForegroundColor DarkYellow
  } else {
    if ($NoVerify) {
      git commit --no-verify -m $msg
    } else {
      git commit -m $msg
    }
  }
}

# 6) Определить ветку и пушнуть
if ([string]::IsNullOrWhiteSpace($Branch)) { $Branch = Get-CurrentBranch }
Write-Host "`nPushing to $Remote/$Branch ..." -ForegroundColor Yellow

if ($DryRun) {
  Write-Host "[DRYRUN] Would run: git push $Remote $Branch" -ForegroundColor DarkYellow
} else {
  git push $Remote $Branch
  Write-Host "Push completed." -ForegroundColor Green
}

Write-Host "== publish-mirror : done ==" -ForegroundColor Cyan
