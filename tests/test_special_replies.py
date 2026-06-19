import pytest

from bot.special_replies import match, FRIDAY_REPLY


@pytest.mark.parametrize("text", [
    "Juma muborak",
    "juma muborak bo'lsin",
    "Жума муборак",
    "жума муборак булсин",
    "  JUMA MUBORAK!  ",
    "Aka, juma muborak bo'lsin sizga",
])
def test_friday_greetings_match(text):
    assert match(text) == FRIDAY_REPLY


@pytest.mark.parametrize("text", [
    "Привет, как дела?",
    "Расскажи про Python",
    "muborak",
    "",
])
def test_non_greetings_return_none(text):
    assert match(text) is None


def test_reply_text_is_exact():
    assert FRIDAY_REPLY == "Assalomu alaykum. Rahmat, birgalikda bo'lsin☪️"
