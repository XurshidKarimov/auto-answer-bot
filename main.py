"""Точка входа: сборка и запуск Telegram-бота."""

import logging

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

from bot.config import load_config
from bot.handlers import on_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def main():
    load_dotenv()
    config = load_config()

    app = ApplicationBuilder().token(config.telegram_token).build()
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
            on_message,
        )
    )

    logging.getLogger(__name__).info("Бот запущен (polling)")
    # ALL_TYPES включает business_message — иначе бот не получит сообщения
    # из Telegram Business-чатов, которыми управляет за пользователя.
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
