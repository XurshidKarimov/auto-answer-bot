# Congratulation Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Превратить бота в строгий автоответчик: Gemini классифицирует каждое сообщение, бот отвечает только на поздравления (пятничное → фиксированный текст, прочие → взаимное поздравление), на всё остальное молчит.

**Architecture:** Gemini получает промпт-классификатор и возвращает протокол: `IGNORE` (молчать), `FRIDAY` (отдать фиксированный ответ) или произвольный текст (взаимное поздравление). Обработчик `on_message` интерпретирует этот протокол. Детектор по ключевым словам удаляется — классификацию полностью ведёт Gemini.

**Tech Stack:** Python 3.13, python-telegram-bot, google-genai, pytest.

## Global Constraints

- Подпись `ASSISTANT_SIGNATURE = "🤖 Telegram Assistant (автоответчик)"` и память диалога (`ConversationStore`, `/reset`) сохраняются без изменений.
- Пятничный ответ `FRIDAY_REPLY` уходит без подписи и не пишется в историю — как сейчас.
- Поддержка Business-чатов (`effective_message`) и обработка `caption` не должны сломаться.
- При ошибке Gemini бот молчит (только лог), сообщений в чат не шлёт.
- Тесты гоняются через `python -m pytest` из корня репозитория.

---

### Task 1: Упростить special_replies до константы

**Files:**
- Modify: `bot/special_replies.py`
- Test: `tests/test_special_replies.py`

**Interfaces:**
- Produces: `FRIDAY_REPLY: str` (значение неизменно), импортируется из `bot.special_replies`.
- Удаляет: `match()`, `_PATTERNS` — больше не существуют.

- [ ] **Step 1: Переписать тест под константу**

Заменить всё содержимое `tests/test_special_replies.py` на:

```python
from bot.special_replies import FRIDAY_REPLY


def test_reply_text_is_exact():
    assert FRIDAY_REPLY == (
        "Амийн, ё Раббал аламийн! Ушбу муборак кунда Аллоҳ гуноҳларимизни мағфират "
        "қилиб, икки дунё саодатини насиб этсин. Сизга ва оила аъзоларингизга ҳам "
        "хайрли бўлсин🤲"
    )
```

- [ ] **Step 2: Запустить тест — должен упасть на импорте**

Run: `python -m pytest tests/test_special_replies.py -v`
Expected: PASS (константа уже есть). Если в этот момент `match` ещё импортируется где-то — это поправит Task 2/3. Здесь тест зелёный.

- [ ] **Step 3: Удалить match() и _PATTERNS**

Заменить всё содержимое `bot/special_replies.py` на:

```python
"""Фиксированный ответ на пятничное поздравление."""

FRIDAY_REPLY = (
    "Амийн, ё Раббал аламийн! Ушбу муборак кунда Аллоҳ гуноҳларимизни мағфират "
    "қилиб, икки дунё саодатини насиб этсин. Сизга ва оила аъзоларингизга ҳам "
    "хайрли бўлсин🤲"
)
```

- [ ] **Step 4: Запустить тест — должен пройти**

Run: `python -m pytest tests/test_special_replies.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bot/special_replies.py tests/test_special_replies.py
git commit -m "refactor: special_replies хранит только FRIDAY_REPLY"
```

---

### Task 2: Протокол-обработчик в handlers

**Files:**
- Modify: `bot/handlers.py`
- Test: `tests/test_handlers.py`

**Interfaces:**
- Consumes: `FRIDAY_REPLY` из `bot.special_replies`; `ConversationStore`; объект `gemini` с методом `generate(history, user_message) -> str`.
- Produces: `build_message_handler(store, gemini)`, `ASSISTANT_SIGNATURE`, `START_REPLY`, `start`, `reset_factory`. Внутренний helper `_classify(raw: str) -> str` возвращает `"IGNORE"`, `"FRIDAY"` или сам текст поздравления.
- Удаляет: константа `ERROR_REPLY` и любые ответы об ошибке пользователю.

- [ ] **Step 1: Переписать тесты под три ветки + молчание при ошибке**

Заменить всё содержимое `tests/test_handlers.py` на:

```python
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
```

- [ ] **Step 2: Запустить тесты — должны упасть**

Run: `python -m pytest tests/test_handlers.py -v`
Expected: FAIL (старый обработчик шлёт ERROR_REPLY/использует match; импорт `ERROR_REPLY` удалён из теста, новая логика отсутствует).

- [ ] **Step 3: Переписать handlers.py**

Заменить всё содержимое `bot/handlers.py` на:

```python
"""Обработчики команд и сообщений Telegram."""

import logging

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
    return raw.strip().strip(".!…").upper()


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
```

- [ ] **Step 4: Запустить тесты — должны пройти**

Run: `python -m pytest tests/test_handlers.py -v`
Expected: PASS (8 тестов)

- [ ] **Step 5: Commit**

```bash
git add bot/handlers.py tests/test_handlers.py
git commit -m "feat: handlers интерпретируют протокол Gemini (IGNORE/FRIDAY/поздравление)"
```

---

### Task 3: Промпт-классификатор по умолчанию

**Files:**
- Modify: `bot/config.py`
- Modify: `.env.example`
- Modify: `.env`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: `load_config(env)` из `bot.config`.
- Produces: `_DEFAULT_SYSTEM_PROMPT` — текст промпта-классификатора; `Config.system_prompt` берёт его при отсутствии `SYSTEM_PROMPT`.

- [ ] **Step 1: Посмотреть текущий тест конфига**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS — фиксируем зелёную базу перед правкой.

- [ ] **Step 2: Добавить тест дефолтного промпта**

Добавить в конец `tests/test_config.py`:

```python
def test_default_system_prompt_is_classifier():
    from bot.config import load_config
    cfg = load_config({
        "TELEGRAM_BOT_TOKEN": "t",
        "GEMINI_API_KEY": "k",
    })
    assert "FRIDAY" in cfg.system_prompt
    assert "IGNORE" in cfg.system_prompt
```

- [ ] **Step 3: Запустить тест — должен упасть**

Run: `python -m pytest tests/test_config.py::test_default_system_prompt_is_classifier -v`
Expected: FAIL (старый дефолт — про универсального ассистента)

- [ ] **Step 4: Заменить дефолтный промпт в config.py**

В `bot/config.py` заменить блок `_DEFAULT_SYSTEM_PROMPT = (...)` на:

```python
_DEFAULT_SYSTEM_PROMPT = (
    "Ты — фильтр автоответчика. На вход приходит сообщение из чата. "
    "Действуй строго по правилам:\n"
    "1. Если это пятничное поздравление («Juma muborak», «Жума муборак» "
    "и любые их варианты) — ответь ровно одним словом: FRIDAY\n"
    "2. Если это любое другое поздравление (с праздником, днём рождения, "
    "событием и т.п.) — напиши короткое тёплое взаимное поздравление в ответ, "
    "на языке отправителя.\n"
    "3. Во всех остальных случаях (вопросы, просьбы, обсуждения, болтовня, "
    "команды и любой другой текст) — ответь ровно одним словом: IGNORE\n"
    "Не добавляй пояснений. Не выводи ничего, кроме указанного."
)
```

- [ ] **Step 5: Запустить тесты конфига — должны пройти**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 6: Обновить SYSTEM_PROMPT в .env.example и .env**

В `.env.example` заменить строку `SYSTEM_PROMPT=...` на (одной строкой, `\n` экранировать не нужно — это образец, бот использует дефолт из config при отсутствии переменной):

```
SYSTEM_PROMPT=Ты — фильтр автоответчика. 1) Пятничное поздравление («Juma muborak»/«Жума муборак» и варианты) → ответь ровно: FRIDAY. 2) Любое другое поздравление → короткое тёплое взаимное поздравление на языке отправителя. 3) Всё остальное → ответь ровно: IGNORE. Ничего кроме указанного не выводи.
```

То же значение записать в `.env` (строка `SYSTEM_PROMPT=...`). Если переменной в `.env` нет — добавить её.

- [ ] **Step 7: Commit**

```bash
git add bot/config.py tests/test_config.py .env.example .env
git commit -m "feat: системный промпт-классификатор поздравлений по умолчанию"
```

---

### Task 4: Прогон всего пакета и обновление README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: всё из Task 1–3.

- [ ] **Step 1: Прогнать весь набор тестов**

Run: `python -m pytest -v`
Expected: PASS — все тесты зелёные.

- [ ] **Step 2: Обновить описание поведения в README**

Найти в `README.md` раздел, описывающий поведение бота (универсальный ассистент / пятничные поздравления), и привести его к новому поведению: бот — автоответчик, Gemini классифицирует сообщения; отвечает только на поздравления (пятничное → фиксированный текст, прочие → взаимное поздравление), на остальное молчит. Если такого раздела нет — добавить короткий абзац «## Поведение» с этим описанием.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README описывает поведение фильтра поздравлений"
```
