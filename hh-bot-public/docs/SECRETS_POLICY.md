# Политика работы с секретами

- Источник значений — Vault/Secrets Manager (prod) и локальный `.env.local` (dev). В репозитории значения **никогда** не храним.
- `.env.example` содержит только ключи; перед запуском заполните обязательные переменные (`BASE_URL`, `DATABASE_URL`, `SECRET_KEY`, `ADMIN_*`, `TELEGRAM_BOT_TOKEN`, `YOOMONEY_WEBHOOK_SECRET`, `REDIS_URL`, `CF_TUNNEL_TOKEN`).
- Скрипт `backend.app.core.startup_checks.ensure_no_placeholders` валидирует ENV на старте и падает, если ключи не заданы или содержат плейсхолдеры.
- Запуск приложений в CI/CD выполняется через Vault: секреты прокидываются в окружение контейнера, `.env` не монтируется.
- При необходимости локального теста создайте `.env.local`, не добавляйте его в git (уже в `.gitignore`).
