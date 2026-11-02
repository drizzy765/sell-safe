import pytest

from app.agent.reply_check import ReplyCheckError, check_reply


def test_allows_tool_price() -> None:
    reply = "The black bag is ₦15,000."
    assert check_reply(reply, language="en", allowed_prices_kobo={1_500_000}) == reply


def test_rejects_invented_price() -> None:
    with pytest.raises(ReplyCheckError):
        check_reply("The bag is ₦25,000.", language="en", allowed_prices_kobo={1_500_000})


def test_rejects_false_payment_confirmed() -> None:
    with pytest.raises(ReplyCheckError):
        check_reply("Payment confirmed.", language="en")


def test_allows_confirmed_with_verdict() -> None:
    reply = "Payment confirmed."
    assert check_reply(reply, language="en", verdict="CONFIRMED") == reply


def test_rejects_long_account_number() -> None:
    with pytest.raises(ReplyCheckError):
        check_reply("Send to 1234567890.", language="en")


def test_allows_tool_account_number() -> None:
    reply = "Transfer to Mama Timi / Opay / 1234567890."
    assert (
        check_reply(
            reply,
            language="en",
            allowed_account_numbers={"1234567890"},
        )
        == reply
    )
