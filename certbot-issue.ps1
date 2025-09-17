param(
  [Parameter(Mandatory=$true)][string]$Email,
  [string]$Domain = "hhoffer.ru",
  [string]$Www    = "www.hhoffer.ru"
)
$ErrorActionPreference='Stop'
Write-Host "== certbot: issue ==" -ForegroundColor Cyan

# 0) гарантируем HTTP-конфиг и живой nginx
Copy-Item .\nginx\nginx.http.conf .\nginx\nginx.conf -Force
docker compose up -d --no-deps --force-recreate nginx | Out-Host

# 1) DNS должен указывать на наш внешний IPv4
$want = (Invoke-RestMethod https://api.ipify.org?format=json).ip
$names = @($Domain,$Www)
$bad = @()
foreach($n in $names){
  $a = (Resolve-DnsName $n -Type A -ErrorAction SilentlyContinue | Select-Object -ExpandProperty IPAddress)
  if(-not $a -or $a -ne $want){ $bad += $n }
}
if($bad.Count){
  Write-Warning "DNS не указывает на твой IP ($want): $($bad -join ', ')"
  Write-Warning "Сертификат не выпустится - сначала поправь A-записи и подожди TTL."
  return
}

# 2) Выпуск через webroot
docker compose run --rm certbot certonly `
  --webroot -w /var/www/certbot `
  -d $Domain -d $Www `
  --agree-tos -m $Email -n | Out-Host
