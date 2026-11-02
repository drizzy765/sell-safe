"""Drive filename convention: Name - NGN price.jpg"""

from app.onboarding.price_parse import parse_filename_product


def test_parse_filename_honey_beans() -> None:
    name, price = parse_filename_product("Honey beans - NGN 6000.jpg")
    assert name == "Honey beans"
    assert price == 6000


def test_parse_filename_with_comma() -> None:
    name, price = parse_filename_product("Mama Gold Rice 5kg - NGN 9,500.jpeg")
    assert name == "Mama Gold Rice 5kg"
    assert price == 9500


def test_parse_filename_naira_symbol() -> None:
    name, price = parse_filename_product("Garri - ₦4200.png")
    assert name == "Garri"
    assert price == 4200


def test_parse_filename_rejects_plain() -> None:
    name, price = parse_filename_product("random-photo.jpg")
    assert name is None
    assert price is None
