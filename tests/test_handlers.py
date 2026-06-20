import asyncio
from unittest.mock import AsyncMock, MagicMock

from bot.handlers import build_message_handler, ASSISTANT_SIGNATURE
from bot.memory import ConversationStore
from bot.special_replies import FRIDAY_REPLY


def _make_update(chat_id, text, caption=None):
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.effective_message.text = text
    update.effective_message.caption = caption
    update.effective_message.reply_text = AsyncMock()
    return update


def test_ignore_token_stays_silent():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = "IGNORE"
    handler = build_message_handler(store, gemini)
    update = _make_update(1, "Расскажи про Python")

    asyncio.run(handler(update, MagicMock()))

    update.effective_message.reply_text.assert_not_called()
    assert store.get(1) == []


def test_ignore_token_is_robust_to_case_and_punctuation():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = "  Ignore.  "
    handler = build_message_handler(store, gemini)
    update = _make_update(8, "сколько времени?")

    asyncio.run(handler(update, MagicMock()))

    update.effective_message.reply_text.assert_not_called()
    assert store.get(8) == []


def test_friday_token_sends_fixed_reply_without_signature_or_history():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = "FRIDAY"
    handler = build_message_handler(store, gemini)
    update = _make_update(2, "Juma muborak")

    asyncio.run(handler(update, MagicMock()))

    update.effective_message.reply_text.assert_awaited_once_with(FRIDAY_REPLY)
    assert store.get(2) == []


def test_congratulation_text_sent_with_signature_and_saved():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = "Спасибо, и вас с праздником!"
    handler = build_message_handler(store, gemini)
    update = _make_update(3, "С Новым годом!")

    asyncio.run(handler(update, MagicMock()))

    gemini.generate.assert_called_once_with(history=[], user_message="С Новым годом!")
    update.effective_message.reply_text.assert_awaited_once_with(
        f"Спасибо, и вас с праздником!\n\n{ASSISTANT_SIGNATURE}"
    )
    assert store.get(3) == [
        {"role": "user", "text": "С Новым годом!"},
        {"role": "model", "text": "Спасибо, и вас с праздником!"},
    ]


def test_caption_message_processed_as_text():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = "IGNORE"
    handler = build_message_handler(store, gemini)
    update = _make_update(4, text=None, caption="что на видео?")

    asyncio.run(handler(update, MagicMock()))

    gemini.generate.assert_called_once_with(history=[], user_message="что на видео?")
    update.effective_message.reply_text.assert_not_called()


def test_message_without_text_or_caption_is_ignored():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    handler = build_message_handler(store, gemini)
    update = _make_update(5, text=None, caption=None)

    asyncio.run(handler(update, MagicMock()))

    gemini.generate.assert_not_called()
    update.effective_message.reply_text.assert_not_called()
    assert store.get(5) == []


def test_business_message_handled_via_effective_message():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = "Поздравляю взаимно!"
    handler = build_message_handler(store, gemini)
    update = _make_update(7, "С днём рождения!")
    update.message = None  # как в бизнес-апдейте

    asyncio.run(handler(update, MagicMock()))

    update.effective_message.reply_text.assert_awaited_once_with(
        f"Поздравляю взаимно!\n\n{ASSISTANT_SIGNATURE}"
    )
    assert store.get(7) == [
        {"role": "user", "text": "С днём рождения!"},
        {"role": "model", "text": "Поздравляю взаимно!"},
    ]


def test_gemini_error_stays_silent():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.side_effect = RuntimeError("boom")
    handler = build_message_handler(store, gemini)
    update = _make_update(6, "привет")

    asyncio.run(handler(update, MagicMock()))

    update.effective_message.reply_text.assert_not_called()
    assert store.get(6) == []


def test_ignore_token_with_question_mark():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = "Ignore?"
    handler = build_message_handler(store, gemini)
    update = _make_update(9, "Что-нибудь")

    asyncio.run(handler(update, MagicMock()))

    update.effective_message.reply_text.assert_not_called()
    assert store.get(9) == []


def test_friday_token_with_exclamation():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = "FRIDAY!"
    handler = build_message_handler(store, gemini)
    update = _make_update(10, "Juma muborak")

    asyncio.run(handler(update, MagicMock()))

    update.effective_message.reply_text.assert_awaited_once_with(FRIDAY_REPLY)
    assert store.get(10) == []


def test_empty_gemini_output_stays_silent():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = ""
    handler = build_message_handler(store, gemini)
    update = _make_update(11, "Привет")

    asyncio.run(handler(update, MagicMock()))

    update.effective_message.reply_text.assert_not_called()
    assert store.get(11) == []


def test_none_gemini_output_stays_silent():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    gemini.generate.return_value = None
    handler = build_message_handler(store, gemini)
    update = _make_update(12, "Привет")

    asyncio.run(handler(update, MagicMock()))

    update.effective_message.reply_text.assert_not_called()
    assert store.get(12) == []
