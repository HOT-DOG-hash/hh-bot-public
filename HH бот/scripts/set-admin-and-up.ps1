New-Item -ItemType Directory -Path ".\scripts" -Force | Out-Null
@'
Param(
  [string]$AppPath = "C:\git-public\hh-bot-public\HH бот",
  [string]$AdminUser = "admin",
  [string]$AdminPass = "admin"
)

function Ensure-EnvKV {
  param([string]$File,[string]$Key,[string]$Value)
  if (-not (Test-Path -LiteralPath $File)) {
    New-Item -ItemType File -Path $File -Force | Out-Null
  }
  $content = Get-Content -LiteralPath $File -Raw -ErrorAction SilentlyContinue
  if ($null -eq $content) { $content = "" }
  if ($content -match "(?m)^\s*$Key\s*=") {
    $content = [System.Text.RegularExpressions.Regex]::Replace(
      $content, "(?m)^\s*$Key\s*=.*$", "$Key=$Value"
    )
  } else {
    if ($content.Length -gt 0 -and -not $content.EndsWith([Environment]::NewLine)) {
      $content += [Environment]::NewLine
    }
    $content += "$Key=$Value" + [Environment]::NewLine
  }
  Set-Content -LiteralPath $File -Value $content -Encoding UTF8 -NoNewline
}

function Invoke-Compose {
  param([string[]]$Args)
  $usesV2 = $false
  try { & docker compose version 2>$null | Out-Null; $usesV2 = $true } catch { $usesV2 = $false }
  if ($usesV2) { & docker compose @Args } else { & docker-compose @Args }
  if ($LASTEXITCODE -ne 0) { throw "Docker compose завершился с ошибкой (код $LASTEXITCODE)." }
}

Write-Host ">> Path: $AppPath"
if (-not (Test-Path -LiteralPath $AppPath)) { throw "Папка не найдена: $AppPath" }

$envFile = Join-Path $AppPath ".env.dev"
Ensure-EnvKV -File $envFile -Key "ADMIN_USER" -Value $AdminUser
Ensure-EnvKV -File $envFile -Key "ADMIN_PASS" -Value $AdminPass

Write-Host "----- .env.dev (ADMIN_*) -----"
(Get-Content -LiteralPath $envFile) |
  Where-Object { $_ -match '^(ADMIN_USER|ADMIN_PASS)=' } |
  ForEach-Object { Write-Host $_ }
Write-Host "------------------------------"

Set-Location -LiteralPath $AppPath
Write-Host ">> docker compose up -d --build"
Invoke-Compose @("up","-d","--build")

Write-Host "`nOK: контейнеры подняты. Открой http://localhost/ и /admin/"
'@ | Set-Content -Path ".\scripts\set-admin-and-up.ps1" -Encoding UTF8
