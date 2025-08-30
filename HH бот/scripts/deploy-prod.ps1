Param(
  # Папка с docker-compose.yml (по умолчанию — как на сервере; на Windows подставь свой путь)
  [string]$AppPath = "/opt/hh-bot-public/HH бот",

  # Админ-доступ для Basic Auth (на проде обязательно поменяй)
  [string]$AdminUser = "admin",
  [string]$AdminPass = "admin",

  # Проверить API после запуска
  [switch]$CheckApi = $true
)

# ===== Helpers =====
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
  try {
    & docker compose version 2>$null | Out-Null
    $usesV2 = $true
  } catch { $usesV2 = $false }

  if ($usesV2) {
    & docker compose @Args
  } else {
    & docker-compose @Args
  }

  if ($LASTEXITCODE -ne 0) {
    throw "Docker compose завершился с ошибкой (код $LASTEXITCODE)"
  }
}

# ===== Main =====
Write-Host ">> AppPath: $AppPath"
if (-not (Test-Path -LiteralPath $AppPath)) {
  throw "Папка не найдена: $AppPath"
}

$composeFile = Join-Path $AppPath "docker-compose.yml"
$envDev     = Join-Path $AppPath ".env.dev"
$envProd    = Join-Path $AppPath ".env.prod"

if (-not (Test-Path -LiteralPath $composeFile)) {
  throw "Не найден $composeFile"
}

# 1) Патчим .env.prod только по ADMIN_*
Ensure-EnvKV -File $envProd -Key "ADMIN_USER" -Value $AdminUser
Ensure-EnvKV -File $envProd -Key "ADMIN_PASS" -Value $AdminPass

Write-Host "`n-- .env.prod (ADMIN_*) --"
(Get-Content -LiteralPath $envProd) |
  Where-Object { $_ -match '^(ADMIN_USER|ADMIN_PASS)=' } |
  ForEach-Object { Write-Host $_ }

# 2) Если compose жёстко смотрит в .env.dev — подменим его содержимым .env.prod
$needsCopy = $false
$composeText = Get-Content -LiteralPath $composeFile -Raw
if ($composeText -match "(?m)^\s*env_file:\s*\.env\.dev\s*$") {
  $needsCopy = $true
}

if ($needsCopy) {
  Write-Host "`n>> Обнаружен env_file: .env.dev в $composeFile — копирую .env.prod -> .env.dev"
  Copy-Item -LiteralPath $envProd -Destination $envDev -Force
} else {
  Write-Host "`n>> env_file в compose параметризован — копию .env.dev делать не нужно."
}

# 3) Запуск
Set-Location -LiteralPath $AppPath
Write-Host "`n>> docker compose up -d --build"
Invoke-Compose @("up","-d","--build")

# 4) (опционально) Проверка API админки
if ($CheckApi) {
  try {
    $bytes  = [Text.Encoding]::ASCII.GetBytes("$AdminUser`:$AdminPass")
    $b64    = [Convert]::ToBase64String($bytes)
    $headers = @{ Authorization = "Basic $b64" }

    # На сервере адрес может отличаться; если за reverse-proxy — подставь свой.
    $url = "http://localhost/api/admin/metrics"

    Write-Host "`n>> Проверка $url"
    $resp = Invoke-WebRequest -Uri $url -Headers $headers -UseBasicParsing -TimeoutSec 10
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) {
      Write-Host "OK: $($resp.StatusCode)"
      Write-Host $resp.Content
    } else {
      Write-Warning "Неожиданный статус: $($resp.StatusCode)"
    }
  } catch {
    Write-Warning "Проверка API не удалась: $($_.Exception.Message)"
  }
}

Write-Host "`nГотово: стек поднят. Проверьте http://<ваш-домен>/ и /admin/"
