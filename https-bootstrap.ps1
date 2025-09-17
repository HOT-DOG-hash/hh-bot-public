param(
  [Parameter(Mandatory=$true)][string]$Email,
  [string]$Domain = "hhoffer.ru",
  [string]$Www    = "www.hhoffer.ru"
)
$ErrorActionPreference = "Stop"
Write-Host "== HTTPS bootstrap for $Domain ==" -ForegroundColor Cyan

# 1) HTTP-конфиг активен
Copy-Item .\nginx\nginx.http.conf .\nginx\nginx.conf -Force
docker compose up -d --no-deps --force-recreate nginx | Out-Host

# 2) DNS check
$want = (Invoke-RestMethod https://api.ipify.org?format=json).ip
$names = @($Domain,$Www)
$bad = @()
foreach($n in $names){
  $a = @(Resolve-DnsName $n -Type A -ErrorAction SilentlyContinue | Select-Object -ExpandProperty IPAddress)
  if(-not $a.Count -or ($a -notcontains $want)){ $bad += $n }
}
if($bad.Count){
  Write-Warning "DNS не указывает на твой IP ($want): $($bad -join ', ')"
  Write-Warning "Останов: поправь A-записи и подожди TTL."
  return
}

# 3) ACME webroot self-test
Write-Host "`n== ACME webroot self-test ==" -ForegroundColor Yellow
$tok = (Get-Random).ToString()
docker compose exec nginx sh -lc "mkdir -p /var/www/certbot/.well-known/acme-challenge && echo ping > /var/www/certbot/.well-known/acme-challenge/$tok" | Out-Null
curl -sS "http://127.0.0.1/.well-known/acme-challenge/$tok" | Out-Host

# 4) Выпуск сертификатов
Write-Host "`n== certbot: issue certs ==" -ForegroundColor Yellow
docker compose run --rm certbot certonly --webroot -w /var/www/certbot `
  -d $Domain -d $Www --agree-tos -m $Email -n | Out-Host

# 5) Проверка наличия сертификатов (внутри nginx)
Write-Host "`n== check live certs inside nginx ==" -ForegroundColor Yellow
docker compose exec nginx sh -lc "ls -l /etc/letsencrypt/live/$Domain && openssl x509 -in /etc/letsencrypt/live/$Domain/fullchain.pem -noout -subject -enddate" | Out-Host

# 6) Переключаем HTTPS
Copy-Item .\nginx\nginx.https.conf .\nginx\nginx.conf -Force
docker compose up -d --no-deps --force-recreate nginx | Out-Host

# 7) Финальные проверки
Write-Host "`n== final checks ==" -ForegroundColor Yellow
curl -sSI "http://$Domain/healthz" | Out-Host
curl -sSI "http://$Www/healthz" | Out-Host
curl -sSI "https://$Domain/healthz" | Out-Host
curl -sSI "https://$Www/healthz" | Out-Host

Write-Host "`nDone." -ForegroundColor Green
