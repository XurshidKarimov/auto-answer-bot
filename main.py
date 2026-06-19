"""Точка входа: сборка и запуск Telegram-бота."""

import logging

from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.config import load_config
from bot.gemini_client import GeminiClient
from bot.handlers import build_message_handler, reset_factory, start
from bot.memory import ConversationStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def main():
    load_dotenv()
    config = load_config()

    store = ConversationStore(max_history=config.max_history)
    gemini = GeminiClient(
        api_key=config.gemini_api_key,
        model=config.gemini_model,
        system_prompt=config.system_prompt,
    )

    app = ApplicationBuilder().token(config.telegram_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset_factory(store)))
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
            build_message_handler(store, gemini),
        )
    )

    logging.getLogger(__name__).info("Бот запущен (polling)")
    app.run_polling()


if __name__ == "__main__":
    main()
