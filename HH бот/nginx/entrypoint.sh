#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${ADMIN_USER:-}" && -n "${ADMIN_PASS:-}" ]]; then
  htpasswd -bc /etc/nginx/.htpasswd "$ADMIN_USER" "$ADMIN_PASS"
fi

envsubst '\$SERVER_NAME' < /etc/nginx/templates/nginx.conf.tpl > /etc/nginx/conf.d/default.conf

nginx -g 'daemon off;'
