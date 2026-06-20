"""Обработчики команд и сообщений Telegram."""

import logging
import string

from bot.memory import ConversationStore
from bot.special_replies import FRIDAY_REPLY

logger = logging.getLogger(__name__)

START_REPLY = "Привет! Я автоответчик. Отвечаю только на поздравления."
# Подпись внизу AI-ответа: показывает, что отвечает автоответчик
ASSISTANT_SIGNATURE = "🤖 Telegram Assistant (автоответчик)"

# Токены протокола, которые возвращает Gemini
_IGNORE = "IGNORE"
_FRIDAY = "FRIDAY"


async def start(update, context):
    await update.effective_message.reply_text(START_REPLY)


def reset_factory(store: ConversationStore):
    async def reset(update, context):
        store.reset(update.effective_chat.id)
        await update.effective_message.reply_text("История диалога очищена.")
    return reset


def _normalize_token(raw: str) -> str:
    """Привести сырой ответ Gemini к виду для сверки с токенами протокола."""
    return raw.strip().strip(string.punctuation + "…").strip().upper()


def build_message_handler(store: ConversationStore, gemini):
    async def on_message(update, context):
        # effective_message покрывает и обычные, и Business-чаты (business_message),
        # а reply_text сам подставит business_connection_id.
        message = update.effective_message
        chat_id = update.effective_chat.id
        # У пересланного видео/фото текст лежит в caption, а не в text
        text = message.text or message.caption
        if not text:
            return

        try:
            reply = gemini.generate(history=store.get(chat_id), user_message=text)
        except Exception:
            # Бот-автоответчик молчит при сбое: не шлём ошибку в чат
            logger.exception("Ошибка при вызове Gemini")
            return

        token = _normalize_token(reply)
        if token == _IGNORE:
            return
        if token == _FRIDAY:
            await message.reply_text(FRIDAY_REPLY)
            return

        await message.reply_text(f"{reply}\n\n{ASSISTANT_SIGNATURE}")
        # в историю сохраняем чистый ответ без подписи, чтобы не засорять контекст
        store.append(chat_id, "user", text)
        store.append(chat_id, "model", reply)

    return on_message
