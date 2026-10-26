from app.agent.templates import format_naira, parse_naira, saved_product


def test_naira_parse_and_template_use_kobo() -> None:
    assert parse_naira("15000") == 15000
    assert parse_naira("15,000") == 15000
    assert parse_naira("₦15,000") == 15000
    assert parse_naira("NGN15000") == 15000
    assert parse_naira("black bag") is None
    assert format_naira(1_500_000) == "₦15,000"
    assert saved_product("Black tote", 1_500_000) == "Saved Black tote at ₦15,000."
