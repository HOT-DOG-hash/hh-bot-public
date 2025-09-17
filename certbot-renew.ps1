$ErrorActionPreference = "Stop"
Write-Host "== certbot renew ==" -ForegroundColor Cyan
docker compose run --rm certbot renew --webroot -w /var/www/certbot | Out-Host
docker compose exec nginx nginx -s reload
Write-Host "Reloaded nginx." -ForegroundColor Green
