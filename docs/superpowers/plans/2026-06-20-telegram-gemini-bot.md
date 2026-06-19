# Telegram-бот на Gemini Pro — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Telegram-бот, обрабатывающий сообщения через Gemini Pro, ведущий связный диалог и отвечающий фиксированной фразой на пятничные поздравления.

**Architecture:** Асинхронный `python-telegram-bot` (polling). Сообщение проходит детектор пятничных поздравлений (минует AI при совпадении), иначе уходит в `GeminiClient` с историей диалога из `ConversationStore` (в ОЗУ). Модули с одной ответственностью, конфиг из `.env`.

**Tech Stack:** Python 3.11+, `python-telegram-bot` v21+, `google-generativeai`, `python-dotenv`, `pytest`.

## Global Constraints

- Python 3.11+.
- Telegram-библиотека: `python-telegram-bot` v21+ (async), запуск через polling.
- AI-модель по умолчанию: `gemini-2.5-pro` (настраивается через `.env`).
- Фиксированный пятничный ответ (копировать дословно): `Assalomu alaykum. Rahmat, birgalikda bo'lsin☪️`.
- Пятничный обмен НЕ записывается в историю диалога.
- Обязательные `.env`: `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`. При их отсутствии — падение на старте с понятным сообщением.
- Внешние вызовы (Gemini, Telegram) в тестах не выполняются — мокаются.
- Сообщения роли в истории: `"user"` и `"model"`.

---

### Task 1: Каркас проекта и зависимости

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `bot/__init__.py`
- Create: `README.md`

**Interfaces:**
- Consumes: ничего.
- Produces: структуру пакета `bot/`, список зависимостей.

- [ ] **Step 1: Создать `requirements.txt`**

```
python-telegram-bot>=21.0
google-generativeai>=0.8.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Создать `.env.example`**

```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-pro
SYSTEM_PROMPT=Ты — полезный универсальный ассистент. Отвечай кратко и по делу на языке пользователя.
MAX_HISTORY=20
```

- [ ] **Step 3: Создать `.gitignore`**

```
.env
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
```

- [ ] **Step 4: Создать `bot/__init__.py`** (пустой файл)

```python
```

- [ ] **Step 5: Создать `README.md`**

```markdown
# auto-answer-bot

Telegram-бот, обрабатывающий сообщения через Google Gemini Pro.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # заполнить TELEGRAM_BOT_TOKEN и GEMINI_API_KEY
```

## Запуск

```bash
python main.py
```

## Тесты

```bash
pytest -v
```

## Команды бота

- `/start` — приветствие
- `/reset` — очистить историю диалога
- любой текст — ответ через Gemini (помнит контекст)
- пятничное поздравление («Juma muborak» и варианты) — фиксированный ответ
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example .gitignore bot/__init__.py README.md
git commit -m "chore: каркас проекта и зависимости"
```

---

### Task 2: Детектор пятничных поздравлений

**Files:**
- Create: `bot/special_replies.py`
- Test: `tests/test_special_replies.py`
- Create: `tests/__init__.py` (пустой)

**Interfaces:**
- Consumes: ничего.
- Produces: `match(text: str) -> str | None` — возвращает `FRIDAY_REPLY` при совпадении пятничного поздравления, иначе `None`. Константа `FRIDAY_REPLY: str`.

- [ ] **Step 1: Создать `tests/__init__.py`** (пустой файл)

```python
```

- [ ] **Step 2: Написать падающий тест `tests/test_special_replies.py`**

```python
import pytest

from bot.special_replies import match, FRIDAY_REPLY


@pytest.mark.parametrize("text", [
    "Juma muborak",
    "juma muborak bo'lsin",
    "Жума муборак",
    "жума муборак булсин",
    "  JUMA MUBORAK!  ",
    "Aka, juma muborak bo'lsin sizga",
])
def test_friday_greetings_match(text):
    assert match(text) == FRIDAY_REPLY


@pytest.mark.parametrize("text", [
    "Привет, как дела?",
    "Расскажи про Python",
    "muborak",
    "",
])
def test_non_greetings_return_none(text):
    assert match(text) is None


def test_reply_text_is_exact():
    assert FRIDAY_REPLY == "Assalomu alaykum. Rahmat, birgalikda bo'lsin☪️"
```

- [ ] **Step 3: Запустить тест — убедиться, что падает**

Run: `pytest tests/test_special_replies.py -v`
Expected: FAIL с `ModuleNotFoundError: No module named 'bot.special_replies'`

- [ ] **Step 4: Реализовать `bot/special_replies.py`**

```python
"""Детектор пятничных поздравлений с фиксированным ответом."""

FRIDAY_REPLY = "Assalomu alaykum. Rahmat, birgalikda bo'lsin☪️"

# Ключевые фразы пятничного поздравления (латиница и кириллица), в нижнем регистре.
_PATTERNS = (
    "juma muborak",
    "жума муборак",
)


def match(text: str) -> str | None:
    """Вернуть FRIDAY_REPLY, если текст содержит пятничное поздравление, иначе None."""
    if not text:
        return None
    normalized = text.strip().lower()
    for pattern in _PATTERNS:
        if pattern in normalized:
            return FRIDAY_REPLY
    return None
```

- [ ] **Step 5: Запустить тест — убедиться, что проходит**

Run: `pytest tests/test_special_replies.py -v`
Expected: PASS (все параметры)

- [ ] **Step 6: Commit**

```bash
git add bot/special_replies.py tests/test_special_replies.py tests/__init__.py
git commit -m "feat: детектор пятничных поздравлений"
```

---

### Task 3: Хранилище истории диалога

**Files:**
- Create: `bot/memory.py`
- Test: `tests/test_memory.py`

**Interfaces:**
- Consumes: ничего.
- Produces: класс `ConversationStore(max_history: int)` с методами:
  - `get(chat_id: int) -> list[dict]` — список сообщений `{"role": str, "text": str}`.
  - `append(chat_id: int, role: str, text: str) -> None` — добавить сообщение, обрезать до `max_history` последних.
  - `reset(chat_id: int) -> None` — очистить историю чата.

- [ ] **Step 1: Написать падающий тест `tests/test_memory.py`**

```python
from bot.memory import ConversationStore


def test_append_and_get():
    store = ConversationStore(max_history=10)
    store.append(1, "user", "привет")
    store.append(1, "model", "здравствуйте")
    assert store.get(1) == [
        {"role": "user", "text": "привет"},
        {"role": "model", "text": "здравствуйте"},
    ]


def test_get_unknown_chat_returns_empty():
    store = ConversationStore(max_history=10)
    assert store.get(999) == []


def test_history_trimmed_to_max():
    store = ConversationStore(max_history=2)
    for i in range(5):
        store.append(1, "user", f"msg{i}")
    history = store.get(1)
    assert len(history) == 2
    assert history == [
        {"role": "user", "text": "msg3"},
        {"role": "user", "text": "msg4"},
    ]


def test_reset_clears_only_target_chat():
    store = ConversationStore(max_history=10)
    store.append(1, "user", "a")
    store.append(2, "user", "b")
    store.reset(1)
    assert store.get(1) == []
    assert store.get(2) == [{"role": "user", "text": "b"}]
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run: `pytest tests/test_memory.py -v`
Expected: FAIL с `ModuleNotFoundError: No module named 'bot.memory'`

- [ ] **Step 3: Реализовать `bot/memory.py`**

```python
"""Хранилище истории диалога в ОЗУ, с обрезкой по длине."""


class ConversationStore:
    """История сообщений по chat_id. Хранит последние max_history сообщений."""

    def __init__(self, max_history: int):
        self._max_history = max_history
        self._store: dict[int, list[dict]] = {}

    def get(self, chat_id: int) -> list[dict]:
        return self._store.get(chat_id, [])

    def append(self, chat_id: int, role: str, text: str) -> None:
        history = self._store.setdefault(chat_id, [])
        history.append({"role": role, "text": text})
        if len(history) > self._max_history:
            del history[: len(history) - self._max_history]

    def reset(self, chat_id: int) -> None:
        self._store.pop(chat_id, None)
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run: `pytest tests/test_memory.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bot/memory.py tests/test_memory.py
git commit -m "feat: хранилище истории диалога"
```

---

### Task 4: Конфигурация из .env

**Files:**
- Create: `bot/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: ничего.
- Produces: датакласс `Config` с полями `telegram_token: str`, `gemini_api_key: str`, `gemini_model: str`, `system_prompt: str`, `max_history: int`. Функция `load_config(env: dict | None = None) -> Config` — читает из переданного словаря (для тестов) или из `os.environ`; бросает `RuntimeError` с понятным текстом при отсутствии обязательного поля.

- [ ] **Step 1: Написать падающий тест `tests/test_config.py`**

```python
import pytest

from bot.config import load_config


def _full_env():
    return {
        "TELEGRAM_BOT_TOKEN": "tok",
        "GEMINI_API_KEY": "key",
    }


def test_load_with_defaults():
    cfg = load_config(_full_env())
    assert cfg.telegram_token == "tok"
    assert cfg.gemini_api_key == "key"
    assert cfg.gemini_model == "gemini-2.5-pro"
    assert cfg.max_history == 20
    assert cfg.system_prompt  # непустой дефолт


def test_overrides_from_env():
    env = _full_env() | {
        "GEMINI_MODEL": "gemini-2.5-flash",
        "MAX_HISTORY": "4",
        "SYSTEM_PROMPT": "Кастомный промпт",
    }
    cfg = load_config(env)
    assert cfg.gemini_model == "gemini-2.5-flash"
    assert cfg.max_history == 4
    assert cfg.system_prompt == "Кастомный промпт"


def test_missing_token_raises():
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        load_config({"GEMINI_API_KEY": "key"})


def test_missing_api_key_raises():
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        load_config({"TELEGRAM_BOT_TOKEN": "tok"})
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run: `pytest tests/test_config.py -v`
Expected: FAIL с `ModuleNotFoundError: No module named 'bot.config'`

- [ ] **Step 3: Реализовать `bot/config.py`**

```python
"""Загрузка и валидация конфигурации из окружения / .env."""

import os
from dataclasses import dataclass

_DEFAULT_SYSTEM_PROMPT = (
    "Ты — полезный универсальный ассистент. "
    "Отвечай кратко и по делу на языке пользователя."
)


@dataclass
class Config:
    telegram_token: str
    gemini_api_key: str
    gemini_model: str
    system_prompt: str
    max_history: int


def load_config(env: dict | None = None) -> Config:
    """Собрать Config. При отсутствии обязательного поля — RuntimeError."""
    env = os.environ if env is None else env

    token = env.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN в .env")

    api_key = env.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Не задан GEMINI_API_KEY в .env")

    return Config(
        telegram_token=token,
        gemini_api_key=api_key,
        gemini_model=env.get("GEMINI_MODEL", "gemini-2.5-pro"),
        system_prompt=env.get("SYSTEM_PROMPT", _DEFAULT_SYSTEM_PROMPT),
        max_history=int(env.get("MAX_HISTORY", "20")),
    )
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bot/config.py tests/test_config.py
git commit -m "feat: загрузка конфигурации из .env"
```

---

### Task 5: Клиент Gemini

**Files:**
- Create: `bot/gemini_client.py`
- Test: `tests/test_gemini_client.py`

**Interfaces:**
- Consumes: история в формате `list[dict]` со `{"role": "user"|"model", "text": str}` (из `ConversationStore.get`).
- Produces: класс `GeminiClient(api_key: str, model: str, system_prompt: str)` с методом `generate(history: list[dict], user_message: str) -> str`. Внутри конвертирует историю в формат `google-generativeai` (`{"role": ..., "parts": [text]}`), вызывает модель, возвращает `response.text`. Импорт `google.generativeai` — на уровне модуля; в тестах подменяется через `monkeypatch`.

- [ ] **Step 1: Написать падающий тест `tests/test_gemini_client.py`**

```python
import bot.gemini_client as gc
from bot.gemini_client import GeminiClient


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModel:
    last_init = None
    last_history = None
    last_message = None

    def __init__(self, model_name, system_instruction):
        _FakeModel.last_init = {"model": model_name, "system": system_instruction}

    def start_chat(self, history):
        _FakeModel.last_history = history
        return self

    def send_message(self, message):
        _FakeModel.last_message = message
        return _FakeResponse("ответ от gemini")


class _FakeGenai:
    configured_with = None

    @staticmethod
    def configure(api_key):
        _FakeGenai.configured_with = api_key

    GenerativeModel = _FakeModel


def test_generate_returns_text(monkeypatch):
    monkeypatch.setattr(gc, "genai", _FakeGenai)
    client = GeminiClient(api_key="key", model="gemini-2.5-pro", system_prompt="SP")
    result = client.generate(
        history=[{"role": "user", "text": "привет"}, {"role": "model", "text": "здравствуйте"}],
        user_message="как дела?",
    )
    assert result == "ответ от gemini"
    assert _FakeGenai.configured_with == "key"
    assert _FakeModel.last_init == {"model": "gemini-2.5-pro", "system": "SP"}
    assert _FakeModel.last_history == [
        {"role": "user", "parts": ["привет"]},
        {"role": "model", "parts": ["здравствуйте"]},
    ]
    assert _FakeModel.last_message == "как дела?"
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run: `pytest tests/test_gemini_client.py -v`
Expected: FAIL с `ModuleNotFoundError: No module named 'bot.gemini_client'`

- [ ] **Step 3: Реализовать `bot/gemini_client.py`**

```python
"""Обёртка над google-generativeai для генерации ответов."""

import google.generativeai as genai


class GeminiClient:
    """Генерирует ответы Gemini с учётом истории диалога и system prompt."""

    def __init__(self, api_key: str, model: str, system_prompt: str):
        self._api_key = api_key
        self._model_name = model
        self._system_prompt = system_prompt

    def generate(self, history: list[dict], user_message: str) -> str:
        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(
            self._model_name,
            system_instruction=self._system_prompt,
        )
        chat = model.start_chat(history=self._to_genai_history(history))
        response = chat.send_message(user_message)
        return response.text

    @staticmethod
    def _to_genai_history(history: list[dict]) -> list[dict]:
        return [{"role": m["role"], "parts": [m["text"]]} for m in history]
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run: `pytest tests/test_gemini_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bot/gemini_client.py tests/test_gemini_client.py
git commit -m "feat: клиент Gemini"
```

---

### Task 6: Обработчики Telegram

**Files:**
- Create: `bot/handlers.py`
- Test: `tests/test_handlers.py`

**Interfaces:**
- Consumes: `ConversationStore` (Task 3), `GeminiClient` (Task 5), `match` + `FRIDAY_REPLY` (Task 2).
- Produces: фабрика `build_message_handler(store, gemini)` → async-функция `on_message(update, context)`. Также `start(update, context)` и `reset_factory(store)` → `reset(update, context)`. Обработчики используют `update.effective_chat.id` и `update.message.text`, отвечают через `update.message.reply_text(...)`. Логика: пятничное поздравление → фиксированный ответ без записи в историю; иначе вызов Gemini с историей, ответ + запись пары в историю; при исключении Gemini — лог и дружелюбное сообщение.
- Константа `ERROR_REPLY: str` для сообщения об ошибке.

- [ ] **Step 1: Написать падающий тест `tests/test_handlers.py`**

```python
import asyncio
from unittest.mock import AsyncMock, MagicMock

from bot.handlers import build_message_handler, ERROR_REPLY
from bot.memory import ConversationStore
from bot.special_replies import FRIDAY_REPLY


def _make_update(chat_id, text):
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.message.text = text
    update.message.reply_text = AsyncMock()
    return update


def test_friday_greeting_replies_fixed_and_skips_history():
    store = ConversationStore(max_history=10)
    gemini = MagicMock()
    handler = build_message_handler(store, gemini)
    update = _make_update(1, "Juma muborak")

    asyncio.run(handler(update, MagicMock()))

    update.message.reply_text.assert_awaited_once_with(FRIDAY_REPLY)
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
    update.message.reply_text.assert_awaited_once_with("ответ")
    assert store.get(2) == [
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

    update.message.reply_text.assert_awaited_once_with(ERROR_REPLY)
    assert store.get(3) == []
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run: `pytest tests/test_handlers.py -v`
Expected: FAIL с `ModuleNotFoundError: No module named 'bot.handlers'`

- [ ] **Step 3: Реализовать `bot/handlers.py`**

```python
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
        text = update.message.text

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
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run: `pytest tests/test_handlers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bot/handlers.py tests/test_handlers.py
git commit -m "feat: обработчики Telegram"
```

---

### Task 7: Точка входа и сборка приложения

**Files:**
- Create: `main.py`

**Interfaces:**
- Consumes: `load_config` (Task 4), `ConversationStore` (Task 3), `GeminiClient` (Task 5), `start` / `reset_factory` / `build_message_handler` (Task 6).
- Produces: исполняемый `main.py`, запускающий polling. Тестов нет (тонкая склейка протестированных модулей); проверяется ручным запуском.

- [ ] **Step 1: Реализовать `main.py`**

```python
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
        MessageHandler(filters.TEXT & ~filters.COMMAND, build_message_handler(store, gemini))
    )

    logging.getLogger(__name__).info("Бот запущен (polling)")
    app.run_polling()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Проверить импорт и сборку без запуска polling**

Run: `python -c "import ast; ast.parse(open('main.py', encoding='utf-8').read()); print('syntax ok')"`
Expected: `syntax ok`

- [ ] **Step 3: Запустить весь набор тестов**

Run: `pytest -v`
Expected: PASS (все тесты Task 2–6)

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: точка входа и сборка бота"
```

---

## Self-Review

**Spec coverage:**
- Приём/ответ Telegram → Task 6 (handlers) + Task 7 (polling). ✓
- Генерация через Gemini Pro → Task 5. ✓
- Память по chat_id в ОЗУ + обрезка → Task 3. ✓
- Универсальный ассистент, настройка через .env (модель, system prompt) → Task 4. ✓
- Пятничное правило, фиксированный ответ, без записи в историю → Task 2 + Task 6. ✓
- Обязательные .env, падение на старте → Task 4. ✓
- Обработка ошибок Gemini → Task 6. ✓
- Тесты с моками → Task 2–6. ✓
- `/start`, `/reset` → Task 6 + Task 7. ✓

**Placeholder scan:** плейсхолдеров нет; весь код приведён.

**Type consistency:** формат сообщений `{"role", "text"}` единый между `ConversationStore` (Task 3), `GeminiClient._to_genai_history` (Task 5) и handlers (Task 6). `generate(history=..., user_message=...)` вызывается с теми же ключевыми аргументами в Task 6 и определён в Task 5. `match`/`FRIDAY_REPLY` согласованы между Task 2 и Task 6.
