Param(
  [string]$AppPath = "C:\git-public\hh-bot-public\HH бот"
)

# --- .env.dev ---
$envFile = Join-Path $AppPath ".env.dev"
if (!(Test-Path -LiteralPath $envFile)) { New-Item -ItemType File -Path $envFile -Force | Out-Null }
$raw = Get-Content -LiteralPath $envFile -Raw -ErrorAction SilentlyContinue
if ($null -eq $raw) { $raw = "" }

function Set-Or-AddLine([string]$text,[string]$name,[string]$value){
  $re = "(?m)^\s*{0}\s*=.*$" -f [regex]::Escape($name)
  if ($text -match ("(?m)^\s*{0}\s*=" -f [regex]::Escape($name))) {
    return [regex]::Replace($text, $re, ("{0}={1}" -f $name,$value))
  } else {
    if (-not $text.EndsWith("`r`n")) { $text += "`r`n" }
    return $text + ("{0}={1}`r`n" -f $name,$value)
  }
}

$raw = Set-Or-AddLine $raw "ADMIN_USER" "admin"
$raw = Set-Or-AddLine $raw "ADMIN_PASS" "admin"
$raw = Set-Or-AddLine $raw "POSTGRES_USER" "app"
$raw = Set-Or-AddLine $raw "POSTGRES_PASSWORD" "app"
$raw = Set-Or-AddLine $raw "POSTGRES_DB" "app"
$raw = Set-Or-AddLine $raw "DATABASE_URL" "postgresql+asyncpg://app:app@db:5432/app"
$raw = Set-Or-AddLine $raw "REDIS_URL" "redis://cache:6379/0"
Set-Content -LiteralPath $envFile -Value $raw -Encoding UTF8

# --- override для БД: named volume вместо bind-mount ---
$override = @"
version: "3.8"
services:
  db:
    environment:
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - pg_data:/var/lib/postgresql/data
volumes:
  pg_data:
"@

Set-Content -LiteralPath (Join-Path $AppPath "docker-compose.override.yml") -Value $override -Encoding UTF8

# --- рестарт проекта из каталога приложения (без -f, чтобы не сломать кириллицу) ---
Push-Location -LiteralPath $AppPath
docker compose down -v
docker compose up -d --build
Pop-Location
