Param(
  [string]$AppPath = "C:\git-public\hh-bot-public\HH бот"
)

function Set-Or-AddLine([string]$text,[string]$name,[string]$value){
  $re = "(?m)^\s*{0}\s*=.*$" -f [regex]::Escape($name)
  if ($text -match ("(?m)^\s*{0}\s*=" -f [regex]::Escape($name))) {
    return [regex]::Replace($text, $re, ("{0}={1}" -f $name,$value))
  } else {
    if (-not $text.EndsWith("`r`n")) { $text += "`r`n" }
    return $text + ("{0}={1}`r`n" -f $name,$value)
  }
}

function Find-AppModule([string]$Root){
  $pyFiles = Get-ChildItem -LiteralPath $Root -Recurse -Filter *.py -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\(\.venv|venv|__pycache__|tests?|migrations|alembic)\\' }
  foreach($f in $pyFiles){
    $c = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue
    if($c -match 'FastAPI\s*\(' -and $c -match '(?m)^\s*app\s*=\s*FastAPI'){
      $rel = $f.FullName.Substring($Root.Length).TrimStart('\')
      $module = ($rel -replace '\\','/') -replace '\.py$',''
      $module = $module -replace '/','.'
      return "$module:app"
    }
  }
  return "backend.main:app"
}

# 1) APP_MODULE + базовые переменные
$appModule = Find-AppModule -Root $AppPath
$envFile = Join-Path $AppPath ".env.dev"
if (!(Test-Path -LiteralPath $envFile)) { New-Item -ItemType File -Path $envFile -Force | Out-Null }
$raw = Get-Content -LiteralPath $envFile -Raw -ErrorAction SilentlyContinue; if ($null -eq $raw) { $raw = "" }
$raw = Set-Or-AddLine $raw "APP_MODULE" $appModule
$raw = Set-Or-AddLine $raw "WEB_PORT" "8000"
$raw = Set-Or-AddLine $raw "ADMIN_USER" "admin"
$raw = Set-Or-AddLine $raw "ADMIN_PASS" "admin"
$raw = Set-Or-AddLine $raw "POSTGRES_USER" "app"
$raw = Set-Or-AddLine $raw "POSTGRES_PASSWORD" "app"
$raw = Set-Or-AddLine $raw "POSTGRES_DB" "app"
$raw = Set-Or-AddLine $raw "DATABASE_URL" "postgresql+asyncpg://app:app@db:5432/app"
$raw = Set-Or-AddLine $raw "REDIS_URL" "redis://cache:6379/0"
Set-Content -LiteralPath $envFile -Value $raw -Encoding UTF8

# 2) override: БД (named volume) + web с working_dir внутрь "HH бот"
$override = @"
version: "3.8"
services:
  db:
    environment:
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - pg_data:/var/lib/postgresql/data

  web:
    env_file:
      - .env.dev
    working_dir: "/app/HH бот"
    entrypoint: ["python","-m","uvicorn"]
    command: ["$appModule","--host","0.0.0.0","--port","8000"]
    healthcheck:
      test: ["CMD","python","-c","import socket; s=socket.socket(); s.settimeout(1); s.connect(('127.0.0.1', 8000)); s.close()"]
      interval: 10s
      timeout: 3s
      retries: 12
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_healthy

volumes:
  pg_data:
"@
Set-Content -LiteralPath (Join-Path $AppPath "docker-compose.override.yml") -Value $override -Encoding UTF8

# 3) рестарт
Push-Location -LiteralPath $AppPath
docker compose up -d --build
Pop-Location
