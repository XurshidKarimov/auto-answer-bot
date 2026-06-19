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
