# Cloudflare Tunnel Token Handling

Токен Cloudflare Tunnel всегда храним только в файле `secrets/cf_tunnel_token.txt`.

## Обновление токена
- Получите новый Named Tunnel token (ингрессы для `hhoffer.ru`, `www.hhoffer.ru`, `api.hhoffer.ru`).
- Запишите строку в `secrets/cf_tunnel_token.txt` без лишних переводов строк.
- Выполните `docker compose -f docker-compose.prod.yml up -d cloudflared`.
- В логах должны появиться `Registered tunnel connection` и `Updated to new configuration`.

## Ограничения безопасности
- Не хранить токен в `.env*`, git, логах и аргументах команд.
- Использовать переменную `TUNNEL_TOKEN` только как временный фоллбэк внутри контейнера.
- Контролировать права доступа к каталогу `secrets/` (доступ только оператору).
