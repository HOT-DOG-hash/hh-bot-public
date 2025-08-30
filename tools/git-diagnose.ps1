param(
  [string]$RepoPath = ".",
  [switch]$TestPush
)

# ── общие настройки ────────────────────────────────────────────────────────────
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function _ok   ($m){ Write-Host "[OK]   $m" -ForegroundColor Green }
function _warn ($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function _fail ($m){ Write-Host "[FAIL] $m" -ForegroundColor Red }
function _info ($m){ Write-Host "[INFO] $m" -ForegroundColor DarkGray }
function _sec  ($t){ Write-Host "`n=== $t ===" -ForegroundColor Cyan }

function Exec([scriptblock]$cmd, [switch]$IgnoreError) {
  $out = $null
  try {
    $out = & $cmd 2>&1
  } catch {
    if (-not $IgnoreError) { throw }
    $out = $_
  }
  return [string[]]($out | ForEach-Object { $_.ToString() })
}

# ── 0) Git установлен? ────────────────────────────────────────────────────────
_sec "Проверка окружения"
try {
  $gv = (Exec { git --version }) -join " "
  _ok "Git найден: $gv"
} catch {
  _fail "Git не найден в PATH."
  exit 1
}

# ── 1) Перейти в репозиторий ──────────────────────────────────────────────────
$full = Resolve-Path -Path $RepoPath
Set-Location $full
_ok ("Репозиторий: {0}" -f $full)

if (-not (Test-Path ".git")) {
  _fail "Это не git-репозиторий (.git отсутствует)."
  exit 1
}

# ── 2) Базовая информация ─────────────────────────────────────────────────────
_sec "Базовая информация"
$branch = (Exec { git rev-parse --abbrev-ref HEAD }).Trim()
_ok ("Текущая ветка: {0}" -f $branch)

$originUrl = $null
try {
  $originUrl = (Exec { git remote get-url origin }).Trim()
  if ($originUrl) { _ok ("origin: {0}" -f $originUrl) } else { throw }
} catch {
  _warn "Remote 'origin' не настроен."
}

# upstream
$hasUpstream = $false
try {
  # ВАЖНО: '@{u}' в кавычках, иначе PowerShell решит, что это хэш-литерал
  $up = (Exec { git rev-parse --abbrev-ref --symbolic-full-name '@{u}' }) -join "`n"
  if ($LASTEXITCODE -eq 0 -and $up) {
    $hasUpstream = $true
    _ok ("Upstream для {0}: {1}" -f $branch, $up)
  } else {
    _warn ("Upstream не настроен для {0}" -f $branch)
  }
} catch {
  _warn "Upstream не найден."
}

# ── 3) Диагностика коммитов (почему 'не коммитит') ────────────────────────────
_sec "Диагностика коммитов"
$porcelain = Exec { git status --porcelain }
if (-not $porcelain) {
  _warn "Рабочее дерево чистое — изменений для коммита нет."
} else {
  _ok "Есть незакоммиченные изменения."
  $porcelain | ForEach-Object { _info $_ }
}

$staged = Exec { git diff --cached --name-only }
if (-not $staged) {
  _warn "В индексе (staging) нет файлов. Перед коммитом сделай: git add -A"
} else {
  _ok "Файлы в индексе:"
  $staged | ForEach-Object { _info ("  {0}" -f $_) }
}

# незавершённые операции
$mergeHead        = Test-Path ".git\MERGE_HEAD"
$rebaseInProgress = (Test-Path ".git\rebase-apply") -or (Test-Path ".git\rebase-merge")
$cherry           = Test-Path ".git\CHERRY_PICK_HEAD"
if ($mergeHead -or $rebaseInProgress -or $cherry) {
  $flags = @()
  if ($mergeHead)        { $flags += "merge" }
  if ($rebaseInProgress) { $flags += "rebase" }
  if ($cherry)           { $flags += "cherry-pick" }
  _warn ("Обнаружен незавершённый процесс: {0}" -f ($flags -join ", "))
}

# ── 4) Быстрые проверки .gitattributes ────────────────────────────────────────
_sec ".gitattributes (быстрая проверка)"
if (Test-Path ".gitattributes") {
  $lines = Get-Content ".gitattributes" -ErrorAction SilentlyContinue
  $badLeading = @()
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s+') { $badLeading += ($i+1) }
  }
  if ($badLeading.Count -gt 0) {
    _warn (".gitattributes: найден(ы) ведущие пробелы в строках: {0}" -f ($badLeading -join ", "))
    _info "Git может трактовать первый токен как имя атрибута → ошибки 'not a valid attribute name'."
  } else {
    _ok ".gitattributes выглядит корректно (нет ведущих пробелов)."
  }
} else {
  _info ".gitattributes не найден — пропускаю."
}

# ── 5) Поверхностный поиск секретов в отслеживаемых файлах ───────────────────
_sec "Поиск строк, похожих на секреты (поверхностно)"
$patterns = @(
  'OPENAI_API_KEY\s*[:=]\s*["''][A-Za-z0-9._|\-]{20,}',
  'API[_A-Z]*KEY\s*[:=]\s*["''][A-Za-z0-9._|\-]{20,}',
  'SECRET[_A-Z]*\s*[:=]\s*["''][A-Za-z0-9._|\-]{20,}'
)
$hits = @()
$tracked = Exec { git ls-files }
foreach ($f in $tracked) {
  if ($f -match '\.(png|jpg|jpeg|gif|pdf|woff2?|ttf|otf)$') { continue }
  try {
    $content = Get-Content -Raw -LiteralPath $f -ErrorAction SilentlyContinue
    foreach ($p in $patterns) { if ($content -match $p) { $hits += $f; break } }
  } catch {}
}
if ($hits.Count -gt 0) {
  _warn "В рабочих файлах найдены строки, похожие на секреты:"
  ($hits | Select-Object -Unique) | ForEach-Object { _info ("  {0}" -f $_) }
} else {
  _ok "Подозрительных строк не найдено (проверка поверхностная)."
}

# ── 6) Крупные файлы (>50MB) ─────────────────────────────────────────────────
_sec "Крупные файлы (могут ломать push)"
$big = @()
foreach ($f in $tracked) {
  try {
    $sz = (Get-Item -LiteralPath $f).Length
    if ($sz -gt 50MB) { $big += ("{0}  ({1:N1} MB)" -f $f, ($sz/1MB)) }
  } catch {}
}
if ($big.Count -gt 0) {
  _warn "Найдены файлы >50MB (GitHub отбрасывает блобы ~100MB). Подумай о Git LFS:"
  $big | ForEach-Object { _info ("  {0}" -f $_) }
} else {
  _ok "Крупных файлов не обнаружено."
}

# ── 7) Тестовый пуш (безопасный dry-run) ─────────────────────────────────────
if ($TestPush) {
  _sec "Тестовый push (dry-run)"
  if (-not $originUrl) {
    _fail "Нельзя проверить push: origin не настроен."
  } else {
    $out = Exec { git push --dry-run --porcelain origin $branch } -IgnoreError
    $txt = ($out -join "`n")
    if (-not $txt) { _ok "Dry-run прошёл без сообщений." } else { Write-Host $txt }

    # расшифровка частых проблем
    if ($txt -match 'GH013: Repository rule violations') {
      _fail "GitHub Push Protection блокирует push (скорее всего секрет в истории). Удали секрет из коммитов или перепиши историю."
    }
    if ($txt -match 'Push cannot contain secrets') {
      _warn "GitHub сообщает: 'Push cannot contain secrets' — проверь недавние коммиты (config.yml, .env и пр.)."
    }
    if ($txt -match 'not a valid attribute name') {
      _fail "Ошибка .gitattributes: строки с неправильным форматом (чаще — ведущие пробелы/неэкранированные пробелы в путях)."
    }
    if ($txt -match '403|forbidden') {
      _fail "403 Forbidden — проверь права/аутентификацию (PAT/SSH)."
    }
    if ($txt -match 'failed to push some refs') {
      _warn "Удалёнка отклонила push. Возможные причины: секреты, защищённая ветка, нужен rebase."
    }
  }
} else {
  _info "Тестовый push не выполнялся (запусти с -TestPush)."
}

# ── 8) Итог ──────────────────────────────────────────────────────────────────
_sec "Итог"
_ok "Диагностика завершена. Смотри предупреждения выше. Скрипт ничего не менял в репозитории."
