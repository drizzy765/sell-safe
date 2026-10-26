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


def parse_naira(text: str) -> int | None:
    cleaned = text.strip().replace(",", "").replace(" ", "")
    for prefix in ("₦", "NGN", "N"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            break
    if not cleaned.isdigit():
        return None
    return int(cleaned)
