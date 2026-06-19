import asyncio
from unittest.mock import AsyncMock, MagicMock

from bot.handlers import build_message_handler, ERROR_REPLY, ASSISTANT_SIGNATURE
from bot.memory import ConversationStore
from bot.special_replies import FRIDAY_REPLY


def _make_update(chat_id, text, caption=None):
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.effective_message.text = text
    update.effective_message.caption = caption
    update.effective_message.reply_text = AsyncMock()
    return update


def test_friday_greeting_replies_fixed_and_skips_history():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    handler = build_message_handler(store, gemini)
    update = _make_update(1, "Juma muborak")

    asyncio.run(handler(update, MagicMock()))

    update.effective_message.reply_text.assert_awaited_once_with(FRIDAY_REPLY)
    gemini.generate.assert_not_called()
    assert store.get(1) == []


def test_normal_message_calls_gemini_and_saves_history():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = "ответ"
    handler = build_message_handler(store, gemini)
    update = _make_update(2, "привет")

    asyncio.run(handler(update, MagicMock()))

    gemini.generate.assert_called_once_with(history=[], user_message="привет")
    # пользователю уходит ответ с подписью автоответчика
    update.effective_message.reply_text.assert_awaited_once_with(f"ответ\n\n{ASSISTANT_SIGNATURE}")
    # в историю сохраняется чистый ответ без подписи
    assert store.get(2) == [
        {"role": "user", "text": "привет"},
        {"role": "model", "text": "ответ"},
    ]


def test_caption_message_processed_as_text():
    # Пересланное видео с подписью: text=None, текст лежит в caption
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = "ответ"
    handler = build_message_handler(store, gemini)
    update = _make_update(4, text=None, caption="что на видео?")

    asyncio.run(handler(update, MagicMock()))

    gemini.generate.assert_called_once_with(history=[], user_message="что на видео?")
    update.effective_message.reply_text.assert_awaited_once_with(f"ответ\n\n{ASSISTANT_SIGNATURE}")
    assert store.get(4) == [
        {"role": "user", "text": "что на видео?"},
        {"role": "model", "text": "ответ"},
    ]


def test_message_without_text_or_caption_is_ignored():
    # Видео без подписи: ни текста, ни caption — бот молчит
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    handler = build_message_handler(store, gemini)
    update = _make_update(5, text=None, caption=None)

    asyncio.run(handler(update, MagicMock()))

    gemini.generate.assert_not_called()
    update.effective_message.reply_text.assert_not_called()
    assert store.get(5) == []


def test_business_message_handled_via_effective_message():
    # В Telegram Business-чате update.message is None (текст в business_message);
    # обработчик должен работать через effective_message и не падать.
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = "ответ"
    handler = build_message_handler(store, gemini)
    update = _make_update(7, "привет")
    update.message = None  # как в бизнес-апдейте

    asyncio.run(handler(update, MagicMock()))

    gemini.generate.assert_called_once_with(history=[], user_message="привет")
    update.effective_message.reply_text.assert_awaited_once_with(
        f"ответ\n\n{ASSISTANT_SIGNATURE}"
    )
    assert store.get(7) == [
        {"role": "user", "text": "привет"},
        {"role": "model", "text": "ответ"},
    ]


def test_gemini_error_replies_friendly_and_keeps_history_clean():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.side_effect = RuntimeError("boom")
    handler = build_message_handler(store, gemini)
    update = _make_update(3, "привет")

    asyncio.run(handler(update, MagicMock()))

    update.effective_message.reply_text.assert_awaited_once_with(ERROR_REPLY)
    assert store.get(3) == []
