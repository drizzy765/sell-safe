"""Seed fictional demo seller, catalog, buyers, and one confirmed fraud signal.

Usage:
  PYTHONPATH=backend python -m scripts.seed_demo
  PYTHONPATH=backend python -m scripts.seed_demo --memory   # no Supabase
  PYTHONPATH=backend python -m scripts.seed_demo --force-prod  # allow when APP_ENV=production

Refuses production unless --force-prod. Idempotent on business_name + product names.
See docs/demo_data.md.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from uuid import uuid4

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.config import Settings, get_settings  # noqa: E402
from app.db.catalog_store import MemoryCatalogStore  # noqa: E402
from app.db.echo_store import MemoryEchoStore  # noqa: E402
from app.db.fraud_store import MemoryFraudStore  # noqa: E402

SELLER_NAME = "Tolu"
BUSINESS = "Tolu's Bags"
PRODUCTS = [
    ("Black leather tote", 1_500_000, "Lagos everyday tote"),
    ("Brown crossbody", 1_250_000, "Compact crossbody"),
    ("Mini clutch", 800_000, "Evening clutch"),
    ("Travel duffel", 2_200_000, "Weekend duffel"),
]


def _hash_account(last4: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{last4}".encode()).hexdigest()


def seed_memory(settings: Settings) -> dict:
    store = MemoryEchoStore()
    catalog = MemoryCatalogStore()
    fraud = MemoryFraudStore()

    seller_id = store.ensure_seller("demo-tolu-bags")
    details = store.seller_details[seller_id]
    details["name"] = SELLER_NAME
    details["business_name"] = BUSINESS
    details["default_language"] = "pcm"
    details["virtual_account"] = {"bank": "Paystack Test", "last4": "1234"}

    buyer_a = store.ensure_buyer("whatsapp", "demo-buyer-a-pcm")
    buyer_b = store.ensure_buyer("instagram", "demo-buyer-b-yo")
    scammer = store.ensure_buyer("whatsapp", "demo-scammer-c")

    products = []
    for name, price, description in PRODUCTS:
        existing = [
            p for p in catalog.products if p["seller_id"] == seller_id and p["name"] == name
        ]
        if existing:
            products.append(existing[0])
            continue
        catalog.products.append(
            {
                "id": str(uuid4()),
                "seller_id": seller_id,
                "name": name,
                "description": description,
                "price_kobo": price,
                "image_path": f"demo/{name.lower().replace(' ', '-')}.jpg",
            }
        )
        products.append(catalog.products[-1])

    salt = settings.pii_salt or "demo-salt"
    account_hash = _hash_account("9999", salt)
    other_seller = store.ensure_seller("demo-other-seller")
    if not any(s.get("value_hash") == account_hash for s in fraud.signals):
        fraud.insert_signal(
            kind="account_number",
            value_hash=account_hash,
            reported_by_seller_id=other_seller,
            evidence_id=None,
            severity=2,
            confirmed=True,
        )

    return {
        "mode": "memory",
        "seller_id": seller_id,
        "business_name": BUSINESS,
        "product_count": len(products),
        "buyers": {"pcm": buyer_a, "yo": buyer_b, "scammer": scammer},
        "fraud_signals": len(fraud.signals),
        "daily_summary_demo": {
            "orders": 6,
            "paid_kobo": 6_250_000,
            "fakes_caught": 2,
            "saved_kobo": 3_700_000,
            "label": "demo",
        },
    }


def seed_supabase(settings: Settings) -> dict:
    from supabase import create_client

    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase URL and service role key required")

    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    existing = (
        client.table("sellers")
        .select("id,business_name")
        .eq("business_name", BUSINESS)
        .limit(1)
        .execute()
    )
    rows = existing.data or []
    if rows:
        seller_id = rows[0]["id"]
    else:
        created = (
            client.table("sellers")
            .insert(
                {
                    "name": SELLER_NAME,
                    "business_name": BUSINESS,
                    "default_language": "pcm",
                    "channel_ids": {"whatsapp": "demo-tolu-bags", "instagram": "demo-tolu-ig"},
                    "virtual_account": {"bank": "Paystack Test", "last4": "1234"},
                    "settings": {"auto_confirm": False, "reminder_hours": 24, "demo": True},
                }
            )
            .execute()
        )
        seller_id = created.data[0]["id"]

    product_ids = []
    for name, price, description in PRODUCTS:
        found = (
            client.table("products")
            .select("id")
            .eq("seller_id", seller_id)
            .eq("name", name)
            .limit(1)
            .execute()
        )
        if found.data:
            product_ids.append(found.data[0]["id"])
            continue
        created = (
            client.table("products")
            .insert(
                {
                    "seller_id": seller_id,
                    "name": name,
                    "description": description,
                    "price_kobo": price,
                    "currency": "NGN",
                    "stock": 5,
                    "tags": ["demo", "bags"],
                    "active": True,
                }
            )
            .execute()
        )
        product_ids.append(created.data[0]["id"])

    buyers = {}
    for key, channel, external in (
        ("pcm", "whatsapp", "demo-buyer-a-pcm"),
        ("yo", "instagram", "demo-buyer-b-yo"),
        ("scammer", "whatsapp", "demo-scammer-c"),
    ):
        found = (
            client.table("buyers")
            .select("id")
            .eq("channel", channel)
            .eq("external_id", external)
            .limit(1)
            .execute()
        )
        if found.data:
            buyers[key] = found.data[0]["id"]
        else:
            created = (
                client.table("buyers")
                .insert(
                    {
                        "channel": channel,
                        "external_id": external,
                        "display_name": key,
                        "language": "pcm" if key == "pcm" else ("yo" if key == "yo" else "en"),
                    }
                )
                .execute()
            )
            buyers[key] = created.data[0]["id"]

    other = (
        client.table("sellers")
        .select("id")
        .eq("business_name", "Demo Other Seller")
        .limit(1)
        .execute()
    )
    if other.data:
        other_id = other.data[0]["id"]
    else:
        created = (
            client.table("sellers")
            .insert(
                {
                    "name": "Demo Other",
                    "business_name": "Demo Other Seller",
                    "channel_ids": {},
                    "settings": {"demo": True},
                }
            )
            .execute()
        )
        other_id = created.data[0]["id"]

    salt = settings.pii_salt or "demo-salt"
    account_hash = _hash_account("9999", salt)
    signals = (
        client.table("fraud_signals").select("id").eq("value_hash", account_hash).limit(1).execute()
    )
    if not signals.data:
        client.table("fraud_signals").insert(
            {
                "kind": "account_number",
                "value_hash": account_hash,
                "reported_by_seller_id": other_id,
                "severity": 2,
                "confirmed": True,
            }
        ).execute()

    return {
        "mode": "supabase",
        "seller_id": seller_id,
        "business_name": BUSINESS,
        "product_count": len(product_ids),
        "buyers": buyers,
        "fraud_signals": 1,
        "daily_summary_demo": {
            "orders": 6,
            "paid_kobo": 6_250_000,
            "fakes_caught": 2,
            "saved_kobo": 3_700_000,
            "label": "demo",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed Sell-Safe demo data")
    parser.add_argument("--memory", action="store_true", help="Use in-memory stores only")
    parser.add_argument(
        "--force-prod",
        action="store_true",
        help="Allow seeding when APP_ENV/ENVIRONMENT looks like production",
    )
    args = parser.parse_args(argv)
    settings = get_settings()
    env_name = getattr(settings, "app_env", "") or getattr(settings, "environment", "") or ""
    # Also peek process env without importing os into settings
    import os

    env_name = (env_name or os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or "dev").lower()
    if env_name in {"prod", "production"} and not args.force_prod:
        print("Refusing to seed production without --force-prod")
        return 2

    if args.memory or not (settings.supabase_url and settings.supabase_service_role_key):
        result = seed_memory(settings)
    else:
        result = seed_supabase(settings)

    print(
        f"seeded mode={result['mode']} seller={result['business_name']} "
        f"products={result['product_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
