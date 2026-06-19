"""Обёртка над google-genai для генерации ответов."""

from google import genai
from google.genai import types


class GeminiClient:
    """Генерирует ответы Gemini с учётом истории диалога и system prompt."""

    def __init__(self, api_key: str, model: str, system_prompt: str):
        self._client = genai.Client(api_key=api_key)
        self._model_name = model
        self._system_prompt = system_prompt

    def generate(self, history: list[dict], user_message: str) -> str:
        chat = self._client.chats.create(
            model=self._model_name,
            config=types.GenerateContentConfig(system_instruction=self._system_prompt),
            history=self._to_genai_history(history),
        )
        response = chat.send_message(user_message)
        return response.text

    @staticmethod
    def _to_genai_history(history: list[dict]) -> list[dict]:
        return [{"role": m["role"], "parts": [{"text": m["text"]}]} for m in history]
