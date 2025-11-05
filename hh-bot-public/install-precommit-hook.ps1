# install-precommit-hook.ps1
[CmdletBinding()] param()

$hookDir = ".git/hooks"
if (-not (Test-Path $hookDir)){ throw "Не похоже на git-репозиторий (.git/hooks не найден)" }

$hookPath = Join-Path $hookDir "pre-commit"
$hook = @"
#!/usr/bin/env pwsh
# Автопроверка секретов перед коммитом
try {
  & pwsh -NoProfile -File "$(Resolve-Path ./scan-secrets.ps1)" -OutFile "secrets-findings.json" -Quiet
  if (\$LASTEXITCODE -ne 0) {
    Write-Host "pre-commit: найдено критичное — отменяю коммит. См. secrets-findings.json" -ForegroundColor Red
    exit \$LASTEXITCODE
  }
  exit 0
} catch {
  Write-Host "pre-commit: ошибка запуска сканера: \$($_)" -ForegroundColor Red
  exit 2
}
"@
$hook | Set-Content -LiteralPath $hookPath -Encoding UTF8
Write-Host "Установлен pre-commit hook: $hookPath" -ForegroundColor Green
