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
