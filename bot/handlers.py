"""Обработчики команд и сообщений Telegram."""

import logging

from bot.memory import ConversationStore
from bot.special_replies import match

logger = logging.getLogger(__name__)

ERROR_REPLY = "Извините, не удалось обработать запрос, попробуйте ещё раз."
START_REPLY = "Привет! Я ассистент на Gemini. Напишите сообщение — отвечу."


async def start(update, context):
    await update.message.reply_text(START_REPLY)


def reset_factory(store: ConversationStore):
    async def reset(update, context):
        store.reset(update.effective_chat.id)
        await update.message.reply_text("История диалога очищена.")
    return reset


def build_message_handler(store: ConversationStore, gemini):
    async def on_message(update, context):
        chat_id = update.effective_chat.id
        # У пересланного видео/фото текст лежит в caption, а не в text
        text = update.message.text or update.message.caption
        if not text:
            return

        special = match(text)
        if special is not None:
            await update.message.reply_text(special)
            return

        try:
            reply = gemini.generate(history=store.get(chat_id), user_message=text)
        except Exception:
            logger.exception("Ошибка при вызове Gemini")
            await update.message.reply_text(ERROR_REPLY)
            return

        await update.message.reply_text(reply)
        store.append(chat_id, "user", text)
        store.append(chat_id, "model", reply)

    return on_message
