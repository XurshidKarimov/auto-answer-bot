"""Хранилище истории диалога в ОЗУ, с обрезкой по длине."""


class ConversationStore:
    """История сообщений по chat_id. Хранит последние max_history сообщений."""

    def __init__(self, max_history: int):
        self._max_history = max_history
        self._store: dict[int, list[dict]] = {}

    def get(self, chat_id: int) -> list[dict]:
        return self._store.get(chat_id, [])

    def append(self, chat_id: int, role: str, text: str) -> None:
        history = self._store.setdefault(chat_id, [])
        history.append({"role": role, "text": text})
        if len(history) > self._max_history:
            del history[: len(history) - self._max_history]

    def reset(self, chat_id: int) -> None:
        self._store.pop(chat_id, None)
