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
