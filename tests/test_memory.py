from bot.memory import ConversationStore


def test_append_and_get():
    store = ConversationStore(max_history=10)
    store.append(1, "user", "привет")
    store.append(1, "model", "здравствуйте")
    assert store.get(1) == [
        {"role": "user", "text": "привет"},
        {"role": "model", "text": "здравствуйте"},
    ]


def test_get_unknown_chat_returns_empty():
    store = ConversationStore(max_history=10)
    assert store.get(999) == []


def test_history_trimmed_to_max():
    store = ConversationStore(max_history=2)
    for i in range(5):
        store.append(1, "user", f"msg{i}")
    history = store.get(1)
    assert len(history) == 2
    assert history == [
        {"role": "user", "text": "msg3"},
        {"role": "user", "text": "msg4"},
    ]


def test_reset_clears_only_target_chat():
    store = ConversationStore(max_history=10)
    store.append(1, "user", "a")
    store.append(2, "user", "b")
    store.reset(1)
    assert store.get(1) == []
    assert store.get(2) == [{"role": "user", "text": "b"}]
