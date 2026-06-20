from bot.special_replies import FRIDAY_REPLY


def test_reply_text_is_exact():
    assert FRIDAY_REPLY == (
        "Амийн, ё Раббал аламийн! Ушбу муборак кунда Аллоҳ гуноҳларимизни мағфират "
        "қилиб, икки дунё саодатини насиб этсин. Сизга ва оила аъзоларингизга ҳам "
        "хайрли бўлсин🤲"
    )
