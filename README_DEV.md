# HH-Bot — dev notes

## 🔐 Платежный API и метрики (P0.3)
- `POST /api/v1/payments/initiate` — создаёт/возвращает YooMoney-платёж (idempotency по `idempotency_key`), отдаёт `invoice_url`.
- `POST /api/v1/payments/webhook` — принимает события YooMoney, дедуплицирует по `provider_event_id`, обновляет FSM оплаты/подписки.
- `GET /metrics` — Prometheus-метрики (`payments_*`, `webhook_lag_seconds`).

## 🤖 Telegram-бот и квоты (P0.4)
- `/api/v1/billing/plans`, `/api/v1/billing/trial/activate`, `/api/v1/billing/subscription/*`, `/api/v1/quota` покрывают FREE_TRIAL, продление подписок и учёт лимитов.
- Бот построен на `front_bot/*` + `backend/app/telegram`: httpx + ASGITransport, чтобы ходить в REST, как внешний клиент.
- `/start` = мини-лендинг + CTA, `/campaign` — 10 шагов мастера (резюме → страна → регион → график → занятость → профобласти → ключевые слова → область поиска → сопроводительное письмо → предпросмотр).
- Завершение мастера вызывает `/api/v1/quota/consume`, показывает остаток; при нуле — ведёт в `/plans` и создаёт YooMoney-ссылку через `/api/v1/payments/initiate`.
- Команды PTB: `/start`, `/campaign`, `/plans`, `/quota`.
