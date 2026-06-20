"""Загрузка и валидация конфигурации из окружения / .env."""

import os
from dataclasses import dataclass

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
