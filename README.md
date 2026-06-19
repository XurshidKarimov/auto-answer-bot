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
