# Secret Rotation Checklist

The following credentials were previously committed and must be rotated before the next production deploy:

- Cloudflare Tunnel token for `hhoffer.ru`.
- Neon/Postgres `neondb_owner` password (`npg_*` values).
- Telegram Bot token `7865199704:…`.
- YooMoney shop secrets (`sr...` etc.).

Rotation steps:
1. Issue new credentials in the provider console.
2. Update vault/CI secrets and staging/prod hosts.
3. Confirm new values via smoke checks (`cloudflared` logs, `/billing/create`, Telegram webhook).
4. Revoke the leaked tokens.
