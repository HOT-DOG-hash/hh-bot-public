param(
  [string]$User = "admin",
  [string]$Pass = "admin"
)
$ErrorActionPreference = 'Stop'
Write-Host "== htpasswd (bcrypt) ==" -ForegroundColor Cyan
docker run --rm httpd:2.4-alpine sh -lc "htpasswd -nbB $User '$Pass'" | Out-Host
Write-Host "Скопируй строку в nginx/.htpasswd или используй htpasswd-set.ps1" -ForegroundColor Yellow
