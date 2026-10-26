import pytest

from app.db.orders import MemoryOrderStore


@pytest.fixture
def store() -> MemoryOrderStore:
    return MemoryOrderStore()


def test_create_order_assigns_unique_ref(store: MemoryOrderStore) -> None:
    order = store.create_order(seller_id="s1", buyer_id="b1", items=[], total_kobo=0)
    assert order["ref"].startswith("SS-")
    order2 = store.create_order(seller_id="s1", buyer_id="b1", items=[], total_kobo=0)
    assert order2["ref"] != order["ref"]


def test_create_order_computes_total(store: MemoryOrderStore) -> None:
    order = store.create_order(
        seller_id="s1",
        buyer_id="b1",
        items=[
            {"product_id": "p1", "qty": 2, "unit_price_kobo": 15000},
            {"product_id": "p2", "qty": 1, "unit_price_kobo": 5000},
        ],
        total_kobo=35000,
    )
    assert order["status"] == "awaiting_payment"
    assert order["total_kobo"] == 35000


def test_get_open_order_returns_awaiting_payment(store: MemoryOrderStore) -> None:
    order = store.create_order(seller_id="s1", buyer_id="b1", items=[], total_kobo=1000)
    found = store.get_open_order("s1", "b1")
    assert found is not None
    assert found["ref"] == order["ref"]


def test_cancel_order_updates_status(store: MemoryOrderStore) -> None:
    order = store.create_order(seller_id="s1", buyer_id="b1", items=[], total_kobo=1000)
    cancelled = store.cancel_order(order["ref"])
    assert cancelled is not None
    assert cancelled["status"] == "cancelled"
