"""Детектор пятничных поздравлений с фиксированным ответом."""

FRIDAY_REPLY = (
    "Амийн, ё Раббал аламийн! Ушбу муборак кунда Аллоҳ гуноҳларимизни мағфират "
    "қилиб, икки дунё саодатини насиб этсин. Сизга ва оила аъзоларингизга ҳам "
    "хайрли бўлсин🤲"
)

# Ключевые фразы пятничного поздравления (латиница и кириллица), в нижнем регистре.
_PATTERNS = (
    "juma muborak",
    "жума муборак",
)


def match(text: str) -> str | None:
    """Вернуть FRIDAY_REPLY, если текст содержит пятничное поздравление, иначе None."""
    if not text:
        return None
    normalized = text.strip().lower()
    for pattern in _PATTERNS:
        if pattern in normalized:
            return FRIDAY_REPLY
    return None
