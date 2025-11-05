$ErrorActionPreference = 'Stop'
Write-Host "== compose-check ==" -ForegroundColor Cyan

docker compose -f .\docker-compose.yml config *> $null
Write-Host "OK: compose config валиден`n"

Write-Host "Сервисы:" -ForegroundColor DarkGray
docker compose config --services

Write-Host "`nСвертка nginx (volumes/ports):" -ForegroundColor DarkGray
$cfg = docker compose -f .\docker-compose.yml config
$lines = ($cfg | Out-String) -split "`r?`n"
$start = ($lines | Select-String -SimpleMatch "  nginx:" | Select-Object -First 1).LineNumber
if ($start) {
  $window = $lines[($start-1)..([Math]::Min($lines.Length-1,$start+120))]
  $window -join "`n" | Out-Host
} else {
  Write-Warning "Не нашли секцию nginx в свертке."
}
