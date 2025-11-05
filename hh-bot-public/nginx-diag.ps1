$ErrorActionPreference = 'Continue'
Write-Host "== nginx: diag inside container ==" -ForegroundColor Cyan

$cid = (docker compose ps -q nginx).Trim()
if (-not $cid) { Write-Warning "nginx контейнер не найден"; return }

"Capabilities:" | Out-Host
docker inspect $cid --format '{{json .HostConfig.CapAdd}}' | Out-Host

"`n== inside ==" | Out-Host
try {
  docker compose exec nginx sh -lc @'
set -eu
echo "-- whoami --"; whoami || true
echo "-- nginx -t --"; nginx -t || true
echo "-- cache dirs --"; ls -ld /var/cache/nginx /var/cache/nginx/* 2>&1 || true
echo "-- head of conf --"; nginx -T 2>&1 | sed -n "1,120p" || true
echo "-- GET /healthz --"; wget -S -O- http://127.0.0.1/healthz 2>&1 || true
'@ | Out-Host
} catch {
  Write-Warning "exec не удался (контейнер может рестартовать): $($_.Exception.Message)"
}
