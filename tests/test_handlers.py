import asyncio
from unittest.mock import AsyncMock, MagicMock

from bot.handlers import on_message
from bot.special_replies import FRIDAY_REPLY


def _make_update(text, caption=None):
    update = MagicMock()
    update.effective_message.text = text
    update.effective_message.caption = caption
    update.effective_message.reply_text = AsyncMock()
    return update


def test_friday_greeting_gets_fixed_reply():
    update = _make_update("Juma muborak")

    asyncio.run(on_message(update, MagicMock()))

    update.effective_message.reply_text.assert_awaited_once_with(FRIDAY_REPLY)


def test_non_greeting_stays_silent():
    update = _make_update("Salom, qalaysan?")

    asyncio.run(on_message(update, MagicMock()))

    update.effective_message.reply_text.assert_not_called()


def test_caption_friday_greeting_gets_reply():
    # Пересланное видео с подписью: text=None, текст лежит в caption
    update = _make_update(text=None, caption="Aka juma muborak bo'lsin")

    asyncio.run(on_message(update, MagicMock()))

    update.effective_message.reply_text.assert_awaited_once_with(FRIDAY_REPLY)


def test_message_without_text_or_caption_is_ignored():
    # Видео без подписи: ни текста, ни caption — бот молчит
    update = _make_update(text=None, caption=None)

    asyncio.run(on_message(update, MagicMock()))

    update.effective_message.reply_text.assert_not_called()


def test_business_message_handled_via_effective_message():
    # В Telegram Business-чате update.message is None (текст в business_message);
    # обработчик должен работать через effective_message и не падать.
    update = _make_update("жума муборак")
    update.message = None

    asyncio.run(on_message(update, MagicMock()))

    update.effective_message.reply_text.assert_awaited_once_with(FRIDAY_REPLY)
