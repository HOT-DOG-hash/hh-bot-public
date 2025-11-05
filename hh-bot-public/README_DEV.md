# HH-Bot — dev notes

## 🔐 Платежный API и метрики (P0.3)
- `POST /api/v1/payments/initiate` — создаёт/возвращает YooMoney-платёж (idempotency по `idempotency_key`), отдаёт `invoice_url`.
- `POST /api/v1/payments/webhook` — принимает события YooMoney, дедуплицирует по `provider_event_id`, обновляет FSM оплаты и подписки.
- `GET /metrics` — Prometheus-метрики (`payments_*`, `webhook_lag_seconds`).

## 🤖 Telegram-бот и квоты (P0.4)
- `/api/v1/billing/plans`, `/api/v1/billing/trial/activate`, `/api/v1/billing/subscription/*`, `/api/v1/quota` реализуют FREE_TRIAL, продление подписки и контроль лимитов.
- `front_bot/*` + `backend/app/telegram` дают единую точку входа: bot ходит в REST через httpx + ASGITransport (как внешний клиент).
- `/start` = мини-лендинг + CTA; `/campaign` проводит через 10 шагов мастера (резюме → страна → регион → график → занятость → профобласти → ключевые слова → область поиска → сопроводительное письмо → предпросмотр) и запускает отклики.
- Завершение мастера вызывает `/api/v1/quota/consume`, показывает остаток и при нуле ведёт к оплате (`/plans` → `/api/v1/payments/initiate`).
- Команды PTB: `/start`, `/campaign`, `/plans`, `/quota`.
