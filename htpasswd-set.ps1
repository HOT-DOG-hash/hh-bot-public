param(
  [Parameter(Mandatory=$true)][string]$User,
  [Parameter(Mandatory=$true)][string]$Password,
  [string]$HostHeader = "www.hhoffer.ru"
)
$ErrorActionPreference='Stop'
Write-Host "== htpasswd: set & reload nginx ==" -ForegroundColor Cyan

# 1) Пытаемся через Apache httpd (bcrypt)
$line = $null
try {
  Write-Host "Генерирую bcrypt через httpd:2.4-alpine..." -ForegroundColor DarkGray
  $line = docker run --rm httpd:2.4-alpine sh -lc "htpasswd -nbB $User '$Password'"
} catch {
  Write-Warning "Провал через httpd: $_"
}

# 2) Фоллбек: OpenSSL APR1
if (-not $line) {
  Write-Host "Фоллбек: openssl -apr1 в alpine:3" -ForegroundColor DarkGray
  $hash = docker run --rm alpine:3 sh -lc "apk add --no-cache openssl >/dev/null 2>&1 && openssl passwd -apr1 '$Password'"
  if (-not $hash) { throw "Не удалось сгенерировать хеш через openssl" }
  $line = "{0}:{1}" -f $User, $hash
}

# 3) Записываем .htpasswd (чтобы bind-монтирование не падало)
$path = Join-Path .\nginx ".htpasswd"
$line | Set-Content -Path $path -Encoding ascii
Write-Host "Записал: $path" -ForegroundColor Green

# 4) Перечитываем nginx
try {
  docker compose exec nginx nginx -t | Out-Host
  docker compose exec nginx nginx -s reload | Out-Host
} catch {
  Write-Warning "reload не удался, делаю recreate nginx"
  docker compose up -d --no-deps --force-recreate nginx | Out-Host
}

# 5) Самопроверка локально
try {
  $h1 = (& curl -sS -o NUL -w "%{http_code}" -H "Host: $HostHeader" http://127.0.0.1/admin/)
  $h2 = (& curl -sS -u "$User`:$Password" -o NUL -w "%{http_code}" -H "Host: $HostHeader" http://127.0.0.1/admin/)
  Write-Host ("Без авторизации /admin → HTTP=$h1 (ожидаемо 401)")
  Write-Host ("С авторизацией /admin → HTTP=$h2 (ожидаемо 200/301)")
} catch {
  Write-Warning $_
}
