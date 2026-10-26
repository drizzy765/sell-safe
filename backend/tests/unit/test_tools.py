import pytest

from app.agent.tools.catalog import CatalogTools
from app.agent.tools.orders import OrderTools
from app.db.catalog_store import MemoryCatalogStore
from app.db.orders import MemoryOrderStore


@pytest.fixture
def catalog() -> MemoryCatalogStore:
    store = MemoryCatalogStore()
    store.products.append(
        {
            "id": "p1",
            "seller_id": "s1",
            "name": "Black tote",
            "description": "Leather bag",
            "price_kobo": 15000,
        }
    )
    store.products.append(
        {
            "id": "p2",
            "seller_id": "s1",
            "name": "Red shoes",
            "description": "Sneakers",
            "price_kobo": 8000,
        }
    )
    return store


@pytest.fixture
def orders() -> MemoryOrderStore:
    return MemoryOrderStore()


def test_search_catalog_filters_by_seller(catalog: MemoryCatalogStore) -> None:
    tools = CatalogTools("s1", catalog)
    results = tools.search_catalog(query="black")
    assert len(results) == 1
    assert results[0]["name"] == "Black tote"


def test_get_product_enforces_seller_scope(catalog: MemoryCatalogStore) -> None:
    tools = CatalogTools("s2", catalog)
    assert tools.get_product(product_id="p1") is None


def test_create_order_writes_row(catalog: MemoryCatalogStore, orders: MemoryOrderStore) -> None:
    order_tools = OrderTools("s1", "b1", orders)
    order = order_tools.create_order(
        items=[{"product_id": "p1", "qty": 1, "unit_price_kobo": 15000}]
    )
    assert order["status"] == "awaiting_payment"
    assert order["total_kobo"] == 15000
