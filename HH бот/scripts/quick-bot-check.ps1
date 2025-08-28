# Быстрый смоук: токен, файл модуля, наличие хэндлеров, ping к Telegram getMe
function ExecBot([string]$cmd) { docker compose exec -T bot sh -lc $cmd }

Write-Host "== tokens ==" -ForegroundColor Cyan
ExecBot 'printenv | egrep "BOT_TOKEN|TELEGRAM_BOT_TOKEN" || true'

Write-Host "== start module ==" -ForegroundColor Cyan
ExecBot 'python - << "PY"
import importlib, json, httpx
import routers.start as s
print("file:", s.__file__)
print({k: hasattr(s,k) for k in ("start","start_over","link_account","in_development")})
PY
'

Write-Host "== telegram getMe ==" -ForegroundColor Cyan
ExecBot 'python - << "PY"
import os, httpx
token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
url = f"https://api.telegram.org/bot{token}/getMe"
print("GET", url[:60]+"...")
r = httpx.post(url, timeout=10)
print("status:", r.status_code, "ok:", r.json().get("ok"))
PY
'
