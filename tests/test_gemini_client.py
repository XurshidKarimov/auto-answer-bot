import bot.gemini_client as gc
from bot.gemini_client import GeminiClient


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeChats:
    last_create = None
    last_message = None

    def create(self, model, config, history):
        _FakeChats.last_create = {"model": model, "config": config, "history": history}
        return self

    def send_message(self, message):
        _FakeChats.last_message = message
        return _FakeResponse("ответ от gemini")


class _FakeClient:
    last_api_key = None

    def __init__(self, api_key):
        _FakeClient.last_api_key = api_key
        self.chats = _FakeChats()


class _FakeGenai:
    Client = _FakeClient


def test_generate_returns_text(monkeypatch):
    monkeypatch.setattr(gc, "genai", _FakeGenai)
    client = GeminiClient(api_key="key", model="gemini-2.5-pro", system_prompt="SP")
    result = client.generate(
        history=[{"role": "user", "text": "привет"}, {"role": "model", "text": "здравствуйте"}],
        user_message="как дела?",
    )
    assert result == "ответ от gemini"
    assert _FakeClient.last_api_key == "key"
    assert _FakeChats.last_create["model"] == "gemini-2.5-pro"
    # system_prompt передаётся в config как system_instruction
    assert _FakeChats.last_create["config"].system_instruction == "SP"
    # история конвертируется в формат google-genai {"role", "parts": [{"text"}]}
    assert _FakeChats.last_create["history"] == [
        {"role": "user", "parts": [{"text": "привет"}]},
        {"role": "model", "parts": [{"text": "здравствуйте"}]},
    ]
    assert _FakeChats.last_message == "как дела?"
