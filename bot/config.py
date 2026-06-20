"""Загрузка и валидация конфигурации из окружения / .env."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    telegram_token: str


def load_config(env: dict | None = None) -> Config:
    """Собрать Config. При отсутствии токена — RuntimeError."""
    env = os.environ if env is None else env

    token = env.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN в .env")

    return Config(telegram_token=token)
