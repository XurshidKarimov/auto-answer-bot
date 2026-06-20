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


def test_default_system_prompt_is_classifier():
    from bot.config import load_config
    cfg = load_config({
        "TELEGRAM_BOT_TOKEN": "t",
        "GEMINI_API_KEY": "k",
    })
    assert "FRIDAY" in cfg.system_prompt
    assert "IGNORE" in cfg.system_prompt
