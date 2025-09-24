#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://hhoffer.ru}"
ADMIN_USER="${ADMIN_USER:-}" # Допущение: экспортируется из /opt/app/.env перед запуском
ADMIN_PASS="${ADMIN_PASS:-}"

log() { printf '[smoke] %s\n' "$*"; }

log "GET $BASE_URL/healthz"
resp=$(curl -fsSL "$BASE_URL/healthz")
[[ "$resp" =~ ok ]] || { echo "Unexpected /healthz body: $resp" >&2; exit 1; }

log "GET $BASE_URL/health"
code=$(curl -s -o /tmp/health.json -w '%{http_code}' "$BASE_URL/health")
[[ "$code" == "200" ]] || { cat /tmp/health.json >&2; exit 1; }

grep -q '"status":"ok"' /tmp/health.json || { cat /tmp/health.json >&2; exit 1; }

log "GET $BASE_URL/admin/ping (unauthenticated)"
code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/admin/ping")
[[ "$code" == "401" ]] || { echo "Expected 401, got $code" >&2; exit 1; }

if [[ -n "$ADMIN_USER" && -n "$ADMIN_PASS" ]]; then
  log "GET $BASE_URL/admin/ping (basic auth)"
  code=$(curl -s -o /dev/null -w '%{http_code}' -u "$ADMIN_USER:$ADMIN_PASS" "$BASE_URL/admin/ping")
  [[ "$code" == "200" ]] || { echo "Expected 200 with admin creds, got $code" >&2; exit 1; }
else
  log "ADMIN_USER/ADMIN_PASS not exported — skipping authenticated admin probe (Допущение)."
fi

log "Smoke tests passed."
