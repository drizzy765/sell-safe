import pytest

from app.agent.catalog import AskSeller, extract_catalog
from app.llm.fake import FakeProvider

_IMAGE = b"\xff\xd8not-logged"


@pytest.mark.asyncio
async def test_extraction_maps_vision_json() -> None:
    provider = FakeProvider(
        vision={
            "name": "Black tote",
            "description": "Leather tote",
            "suggested_price_kobo": 1500000,
            "category": "bags",
            "colors": ["black"],
            "confidence": 0.8,
        }
    )

    result = await extract_catalog(provider, _IMAGE)

    assert result.name == "Black tote"
    assert result.suggested_price_kobo == 1500000
    assert result.colors == ["black"]
    assert provider.vision_calls[0].count(str(_IMAGE)) == 0


@pytest.mark.asyncio
async def test_null_price_is_allowed() -> None:
    provider = FakeProvider()
    result = await extract_catalog(provider, _IMAGE)
    assert result.suggested_price_kobo is None


@pytest.mark.asyncio
async def test_invalid_json_retries_once_then_asks_seller() -> None:
    retry = FakeProvider(json_failures=1)
    recovered = await extract_catalog(retry, _IMAGE)
    assert recovered.name == "Black tote"
    assert len(retry.vision_calls) == 2
    assert "invalid" in retry.vision_calls[1].lower()

    give_up = FakeProvider(json_failures=2)
    failed = await extract_catalog(give_up, _IMAGE)
    assert isinstance(failed, AskSeller)
    assert len(give_up.vision_calls) == 2
