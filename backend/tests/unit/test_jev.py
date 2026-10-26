import pytest

from app.decisions.fake import FakeJev


@pytest.mark.asyncio
async def test_fake_jev_returns_canned_scores() -> None:
    jev = FakeJev(intent="price_question", language="pcm")
    scores = await jev.ask(text="how much")
    assert scores.intent == "price_question"
    assert scores.language == "pcm"
    assert scores.scam_pressure == 0.0


@pytest.mark.asyncio
async def test_fake_jev_falls_back_to_seller_default_for_other() -> None:
    jev = FakeJev(intent="order", language="other")
    scores = await jev.ask(text="I go take am", seller_default_language="yo")
    assert scores.language == "yo"
