from app.onboarding.price_parse import parse_caption_price_ngn


def test_parse_naira_symbol() -> None:
    price, flags = parse_caption_price_ngn("Fresh garri ₦9,500 delivery Lagos")
    assert price == 9500
    assert flags == []


def test_parse_k_suffix() -> None:
    price, flags = parse_caption_price_ngn("Ankara set 9.5k only")
    assert price == 9500
    assert flags == []


def test_dm_for_price() -> None:
    price, flags = parse_caption_price_ngn("Nice bag. DM for price")
    assert price is None
    assert "dm_for_price" in flags


def test_missing_price() -> None:
    price, flags = parse_caption_price_ngn("Just a vibe")
    assert price is None
    assert "missing_price" in flags
