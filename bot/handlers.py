"""Обработчик сообщений: отвечает только на пятничное поздравление."""

import logging

from bot.special_replies import match

logger = logging.getLogger(__name__)


async def on_message(update, context):
    # effective_message покрывает и обычные, и Business-чаты (business_message),
    # а reply_text сам подставит business_connection_id.
    message = update.effective_message
    # У пересланного видео/фото текст лежит в caption, а не в text
    text = message.text or message.caption
    if not text:
        return

    reply = match(text)
    if reply is None:
        # Не пятничное поздравление — бот молчит
        return
    await message.reply_text(reply)
