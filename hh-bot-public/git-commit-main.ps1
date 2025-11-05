# git-commit-main.ps1
[CmdletBinding()]
param(
  [string]$Message = "chore: update configs and scripts",
  [string]$Branch  = "main",
  [string]$Origin  = "",           # например: https://github.com/HOT-DOG-hash/hh-bot-public.git
  [switch]$AutoInit,               # если нет .git — сделать git init + branch -M + remote add origin
  [switch]$Force,                  # коммит даже если scan нашёл High
  [switch]$SkipScan
)

$ErrorActionPreference = 'Stop'

function Run-Git {
  param([string[]]$Args)
  $out = & git @Args 2>&1
  $code = $LASTEXITCODE
  if ($code -ne 0){
    throw "git $($Args -join ' ') failed ($code):`n$out"
  }
  return $out
}

# 0) git в PATH?
if (-not (Get-Command git -ErrorAction SilentlyContinue)){
  throw "Git не найден в PATH. Установи Git и зайди: https://git-scm.com/"
}

# 1) если нет .git и указан -AutoInit — инициализируем
$inRepo = $false
try { & git rev-parse --is-inside-work-tree *> $null; $inRepo = ($LASTEXITCODE -eq 0) } catch { $inRepo = $false }

if (-not $inRepo){
  if (-not $AutoInit){
    throw "Текущая папка не является git-репозиторием. Запусти с -AutoInit -Origin <URL> или инициализируй вручную (git init)."
  }
  Run-Git @('init')
  # Сразу делаем main
  Run-Git @('branch','-M',$Branch)
  if ([string]::IsNullOrWhiteSpace($Origin)){
    throw "Укажи origin (параметр -Origin), например: https://github.com/HOT-DOG-hash/hh-bot-public.git"
  }
  Run-Git @('remote','add','origin',$Origin)
}

# 2) Скан секретов
if (-not $SkipScan){
  $scan = Join-Path (Get-Location) "scan-secrets.ps1"
  if (-not (Test-Path $scan)){ throw "Не найден $scan — положи его в корень репозитория." }
  & pwsh -NoProfile -File $scan -OutFile "secrets-findings.json" -Quiet
  $code = $LASTEXITCODE
  if ($code -ne 0 -and -not $Force){
    Write-Host "Останавливаю коммит: обнаружены high-секреты (см. secrets-findings.json). Запусти с -Force, если понимаешь риск." -ForegroundColor Red
    exit $code
  }
}

# 3) origin может отсутствовать — предупреждаем (если вручную инициализировали)
try { git remote get-url origin *> $null } catch { Write-Warning "origin ещё не настроен. Укажи -Origin или: git remote add origin <URL>" }

# 4) Подтягиваем обновления и переключаемся/создаем ветку
try { Run-Git @('fetch','origin','--prune') } catch { }

$hasBranch = $true
try { Run-Git @('rev-parse','--verify',$Branch) } catch { $hasBranch = $false }

if ($hasBranch){
  Run-Git @('checkout',$Branch)
  try { Run-Git @('pull','--rebase','origin',$Branch) } catch { }
} else {
  Run-Git @('checkout','-b',$Branch)
}

# 5) Базовый .gitignore (если нет)
$gi = ".gitignore"
if (-not (Test-Path $gi)){
@"
# Python
__pycache__/
*.pyc
.venv/
venv/
# Node
node_modules/
# IDE
.vscode/
.idea/
# Build
dist/
build/
# Docker volumes/sensitives
nginx/.htpasswd
letsencrypt/
certbot-webroot/
.env
.env.*
"@ | Set-Content -LiteralPath $gi -Encoding UTF8
  & git add $gi | Out-Null
}

# 6) add/commit
& git add -A
$status = & git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)){
  Write-Host "Нет изменений для коммита. Нечего пушить." -ForegroundColor Yellow
  exit 0
}
Run-Git @('commit','-m',$Message)

# 7) push
try {
  Run-Git @('push','-u','origin',$Branch)
  Write-Host "✅ Коммит запушен в $Branch." -ForegroundColor Green
} catch {
  Write-Warning "Не удалось выполнить push. Проверь доступ к origin (SSH ключ/PAT) и повтори:
    git push -u origin $Branch"
  throw
}
