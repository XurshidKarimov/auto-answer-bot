import pytest

from bot.config import load_config


def test_load_token():
    cfg = load_config({"TELEGRAM_BOT_TOKEN": "tok"})
    assert cfg.telegram_token == "tok"


def test_missing_token_raises():
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        load_config({})
