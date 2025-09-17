param(
  [Parameter(Mandatory=$true)][string]$Email,
  [string]$Domain = "hhoffer.ru",
  [string]$Www    = "www.hhoffer.ru",
  [string]$OutFile = ""
)

$ErrorActionPreference = 'Continue'
$ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
Write-Host "== Certbot issue & list ($ts) ==" -ForegroundColor Cyan
Write-Host "Domain: $Domain, WWW: $Www, Email: $Email" -ForegroundColor DarkGray

$log = New-Object System.Collections.Generic.List[string]
function Add-Log([string]$s){ $log.Add($s); $s }

# 0) убедимся, что nginx поднят (не критично)
try { docker compose up -d nginx 2>&1 | % { Add-Log $_ } | Out-Host } catch {}

# 1) Запуск certbot-issue.ps1
Write-Host "`n== Running certbot-issue.ps1 ==" -ForegroundColor Yellow | % { Add-Log $_ } | Out-Host
try {
  & pwsh -File .\certbot-issue.ps1 -Email $Email -Domain $Domain -Www $Www 2>&1 |
    % { Add-Log $_ } | Out-Host
} catch {
  Add-Log ("[ERROR] certbot-issue.ps1: " + $_.Exception.Message) | Out-Host
}

# 2) Показать, что лежит в live/archive и метаданные fullchain.pem
Write-Host "`n== Listing live certs inside nginx ==" -ForegroundColor Yellow | % { Add-Log $_ } | Out-Host
try { docker compose up -d nginx 2>&1 | % { Add-Log $_ } | Out-Host } catch {}

$cmd_list = @"
echo '[live]   /etc/letsencrypt/live/$Domain'
ls -la /etc/letsencrypt/live/$Domain || echo 'live dir not found'
echo
echo '[archive] /etc/letsencrypt/archive/$Domain'
ls -la /etc/letsencrypt/archive/$Domain || echo 'archive dir not found'
echo
if [ -f /etc/letsencrypt/live/$Domain/fullchain.pem ]; then
  echo '[openssl x509]'
  openssl x509 -in /etc/letsencrypt/live/$Domain/fullchain.pem -noout -subject -issuer -enddate
else
  echo 'no live cert found (fullchain.pem not present)'
fi
"@

try {
  docker compose exec nginx sh -c "$cmd_list" 2>&1 | % { Add-Log $_ } | Out-Host
} catch {
  Add-Log ("[ERROR] docker compose exec nginx: " + $_.Exception.Message) | Out-Host
}

if($OutFile -and $OutFile.Trim()){
  try {
    $dir = Split-Path -Parent $OutFile
    if($dir -and -not (Test-Path $dir)){ New-Item -ItemType Directory -Path $dir | Out-Null }
    $log | Set-Content -Path $OutFile -Encoding UTF8
    Write-Host "`nSaved log: $OutFile" -ForegroundColor Green
  } catch {
    Write-Host "`n[WARN] can't save log: $($_.Exception.Message)" -ForegroundColor DarkYellow
  }
}

Write-Host "`nDone." -ForegroundColor Green
