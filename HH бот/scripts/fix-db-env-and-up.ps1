Param(
  [string]$AppPath = "C:\git-public\hh-bot-public\HH бот"
)

$envFile = Join-Path $AppPath ".env.dev"
if (!(Test-Path -LiteralPath $envFile)) { New-Item -ItemType File -Path $envFile -Force | Out-Null }
$raw = Get-Content -LiteralPath $envFile -Raw -ErrorAction SilentlyContinue

function Ensure-Line($text, $name, $value){
  if ($text -match ("(?m)^\s*{0}\s*=" -f [regex]::Escape($name))) {
    return $text
  } else {
    if (-not $text.EndsWith("`r`n")) { $text += "`r`n" }
    return $text + ("{0}={1}`r`n" -f $name,$value)
  }
}

# ADMIN_* — уже есть, но на всякий случай
$raw = [regex]::Replace($raw,'(?m)^\s*ADMIN_USER\s*=.*$','ADMIN_USER=admin')
$raw = [regex]::Replace($raw,'(?m)^\s*ADMIN_PASS\s*=.*$','ADMIN_PASS=admin')

# Postgres и Redis по дефолту для dev
$raw = Ensure-Line $raw 'POSTGRES_USER'      'app'
$raw = Ensure-Line $raw 'POSTGRES_PASSWORD'  'app'
$raw = Ensure-Line $raw 'POSTGRES_DB'        'app'
$raw = Ensure-Line $raw 'DATABASE_URL'       'postgresql+asyncpg://app:app@db:5432/app'
$raw = Ensure-Line $raw 'REDIS_URL'          'redis://cache:6379/0'

Set-Content -LiteralPath $envFile -Value $raw -Encoding UTF8

# Из-за кириллицы в пути иногда чудит кодировка — вызываем compose через -f
$composeFile = Join-Path $AppPath "docker-compose.yml"

# ОСТОРОЖНО: удалит dev-данные в том числе у Postgres/Redis (подходит для чистого старта)
docker compose -f $composeFile down -v

docker compose -f $composeFile build --no-cache
docker compose -f $composeFile up -d
