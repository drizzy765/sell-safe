import pytest

from app.config import Settings
from app.decisions.client import TypeSafeClient
from app.decisions.factory import build_jev
from app.decisions.heuristic import HeuristicJev


@pytest.mark.asyncio
async def test_price_question_phrase() -> None:
    scores = await HeuristicJev().ask(text="How much be the bag?")
    assert scores.intent == "price_question"
    assert scores.intent_scores["price_question"] >= 0.85
    assert scores.intent_scores["order"] <= 0.1
    assert scores.image_kind is None
    assert scores.evidence_match == 0.0
    assert scores.receipt_tampered == 0.0


@pytest.mark.asyncio
async def test_order_phrase() -> None:
    scores = await HeuristicJev().ask(text="I go take am")
    assert scores.intent == "order"
    assert scores.language == "en"


@pytest.mark.asyncio
async def test_payment_proof_phrase() -> None:
    scores = await HeuristicJev().ask(text="I have paid")
    assert scores.intent == "payment_proof"
    assert scores.intent_scores["payment_proof"] >= 0.85


@pytest.mark.asyncio
async def test_pidgin_marker() -> None:
    scores = await HeuristicJev().ask(text="Abeg")
    assert scores.language == "pcm"
    assert scores.language_scores["pcm"] >= 0.85
    assert scores.language_scores["en"] <= 0.1


@pytest.mark.asyncio
async def test_yoruba_word() -> None:
    scores = await HeuristicJev().ask(text="Elo ni")
    assert scores.language == "yo"
    assert scores.language_scores["yo"] >= 0.85
    assert scores.language_scores["pcm"] <= 0.1


@pytest.mark.asyncio
async def test_scam_pressure_is_higher_when_buyer_pushes_for_goods() -> None:
    router = HeuristicJev()
    pushed = await router.ask(text="send the goods first")
    calm = await router.ask(text="how much")
    assert pushed.scam_pressure > calm.scam_pressure
    assert pushed.scam_pressure <= 1


def test_empty_typesafe_key_uses_heuristic_router() -> None:
    assert isinstance(build_jev(Settings(typesafe_api_key="")), HeuristicJev)


def test_funded_typesafe_key_uses_typesafe_client() -> None:
    assert isinstance(build_jev(Settings(typesafe_api_key="funded")), TypeSafeClient)
