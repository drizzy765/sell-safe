"""Fixed messages for amounts. The model does not write these sentences."""


def format_naira(price_kobo: int) -> str:
    naira = price_kobo // 100
    return f"₦{naira:,}"


def ask_price(name: str) -> str:
    return f"I see {name}. Reply with the price in naira to save it."


def ask_price_again() -> str:
    return "Reply with the price in naira, like 15000."


def saved_product(name: str, price_kobo: int) -> str:
    return f"Saved {name} at {format_naira(price_kobo)}."


def ask_seller_reread() -> str:
    return "I couldn't read that photo. Send it again."


def fallback_ask_type(language: str) -> str:
    fallbacks = {
        "en": "I couldn't hear that clearly. Please type your message.",
        "pcm": "I no hear am well. Abeg type am.",
        "yo": "N kò gbọ́ rẹ̀ dáadáa. Jọ̀wọ́ kọ ọ sílẹ̀.",
    }
    return fallbacks.get(language, fallbacks["en"])


def confirmed_payment(total_kobo: int, sender_name: str | None, reference: str | None) -> str:
    sender = f" from {sender_name}" if sender_name else ""
    ref = f" ref {reference}" if reference else ""
    return f"Money don land. {format_naira(total_kobo)}{sender}{ref}. You fit release the goods."


def not_found_payment() -> str:
    return (
        "No money yet. Wait for the alert. We go recheck for 30 minutes. "
        "No release the goods until I confirm."
    )


def suspicious_payment(reasons: list[str]) -> str:
    reason_text = ", ".join(reasons) if reasons else "suspicious receipt"
    return f"This receipt looks fake: {reason_text}. Don't release the goods."


def release_card(ref: str, verdict: str) -> str:
    if verdict == "CONFIRMED":
        return f"Order {ref} is CONFIRMED. Goods may leave the shop."
    return f"Order {ref}: {verdict}. Do NOT release goods."


def parse_naira(text: str) -> int | None:
    cleaned = text.strip().replace(",", "").replace(" ", "")
    for prefix in ("₦", "NGN", "N"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            break
    if not cleaned.isdigit():
        return None
    return int(cleaned)
