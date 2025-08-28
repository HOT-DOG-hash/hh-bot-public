import os
import sys
import asyncio
import logging
from logging.handlers import WatchedFileHandler
from pathlib import Path

# Снимок окружения ДО любых импортов «шумных» модулей
ORIG_ENV = dict(os.environ)

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    PicklePersistence,
)

# ─── logging ──────────────────────────────────────────────────────────────────
def setup_logging() -> None:
    """
    «Живучее» логирование:
    - пытаемся писать в файл (по умолчанию /var/log/app/bot.log);
    - если нет прав/пути — не падаем, остаёмся со stdout.
    """
    log_file = os.getenv("BOT_LOG_FILE", "/var/log/app/bot.log")
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    try:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = WatchedFileHandler(log_file, encoding="utf-8")
        handlers.append(fh)
    except Exception as e:  # noqa: BLE001
        # Только stdout/stderr — но приложение живёт
        print(f"[setup_logging] WARN: file logging disabled ({e})", file=sys.stderr)

    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)

# ─── token ────────────────────────────────────────────────────────────────────
def _sanitize(s: str | None) -> str | None:
    if not s:
        return None
    s = s.strip().strip('"').strip("'").strip()
    if s.startswith("<") and s.endswith(">"):
        s = s[1:-1].strip()
    return s or None

def read_token() -> str:
    """
    Приоритет: исходное окружение процесса → текущее окружение.
    Не используем .env, не валимся из-за кавычек/скобок.
    """
    sources = [
        ("ORIG_ENV.TELEGRAM_BOT_TOKEN", ORIG_ENV.get("TELEGRAM_BOT_TOKEN")),
        ("ORIG_ENV.BOT_TOKEN", ORIG_ENV.get("BOT_TOKEN")),
        ("ENV.TELEGRAM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN")),
        ("ENV.BOT_TOKEN", os.getenv("BOT_TOKEN")),
    ]
    invalid = {"TELEGRAM_BOT_TOKEN", "BOT_TOKEN", "changeme", "YOUR_TOKEN_HERE"}

    token = None
    picked = None
    for name, val in sources:
        val = _sanitize(val)
        if val and (":" in val) and (len(val) >= 30) and (val not in invalid):
            token, picked = val, name
            break

    if not token:
        logging.error("TELEGRAM_BOT_TOKEN не задан или некорректный. Задай TELEGRAM_BOT_TOKEN (или BOT_TOKEN) в .env")
        sys.exit(1)

    masked = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "***"
    logging.info("Telegram token загружен из %s (%s)", picked, masked)
    return token

# ─── main ─────────────────────────────────────────────────────────────────────
async def main() -> None:
    setup_logging()
    token = read_token()

    # Дублируем токен обратно в текущее окружение — чтобы любые импортируемые
    # модули (например, config.py) увидели его даже если что-то мутит окружение.
    os.environ["TELEGRAM_BOT_TOKEN"] = token
    os.environ["BOT_TOKEN"] = token

    # Теперь безопасно подключаем роутеры (могут иметь сайд-эффекты)
    from routers import menu, start, letters, responses, auto_responses, stats

    persistence = PicklePersistence(filepath="demo_bot_persistence")
    app = Application.builder().token(token).persistence(persistence).build()

    commands = [
        BotCommand("start", "Начать / Перезапустить"),
        BotCommand("menu", "Главное меню 🧭"),
        BotCommand("responses", "Запустить отклики 🚀"),
        BotCommand("response_message", "Сопроводительные письма ✉️"),
    ]

    responses_conv: ConversationHandler = responses.get_responses_conv_handler()
    cover_letter_conv: ConversationHandler = letters.get_cover_letter_conv_handler()
    auto_responses_conv: ConversationHandler = auto_responses.get_auto_responses_conv_handler()
    stats_conv: ConversationHandler = stats.get_stats_conv_handler()

    app.add_handler(CommandHandler("start", start.start))
    app.add_handler(CommandHandler("menu", menu.main_menu))
    app.add_handler(responses_conv)
    app.add_handler(cover_letter_conv)
    app.add_handler(auto_responses_conv)
    app.add_handler(stats_conv)

    app.add_handler(CallbackQueryHandler(start.link_account, pattern=r"^link_account$"))
    app.add_handler(CallbackQueryHandler(menu.show_subscription, pattern=r"^subscription$"))
    app.add_handler(CallbackQueryHandler(menu.handle_payment_stub, pattern=r"^pay_(week|month)$"))
    app.add_handler(CallbackQueryHandler(menu.show_support, pattern=r"^support$"))
    app.add_handler(CallbackQueryHandler(menu.show_referral_program, pattern=r"^referral$"))
    app.add_handler(CallbackQueryHandler(menu.main_menu, pattern=r"^main_menu$"))

    async with app:
        await app.initialize()
        await app.bot.set_my_commands(commands)
        me = await app.bot.get_me()
        logging.info("Команды установлены. Бот: @%s (id=%s)", me.username, me.id)

        logging.info("Запускаем polling ...")
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
