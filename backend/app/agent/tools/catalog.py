"""Catalog tools. Prices and stock are read from the database."""

from app.db.catalog_store import CatalogStore


class CatalogTools:
    """Tools bound to a seller. The LLM cannot see another seller's catalog."""

    def __init__(self, seller_id: str, catalog: CatalogStore) -> None:
        self._seller_id = seller_id
        self._catalog = catalog

    def search_catalog(self, *, query: str, max_results: int = 5) -> list[dict]:
        """Search the seller's catalog by name or description."""
        return self._catalog.search_products(self._seller_id, query, limit=max_results)

    def get_product(self, *, product_id: str) -> dict | None:
        """Get one product by id."""
        return self._catalog.get_product(self._seller_id, product_id)

    def schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_catalog",
                    "description": "Search the seller's product catalog by name or description.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "max_results": {"type": "integer", "default": 5},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_product",
                    "description": "Get a single product by its id.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                        },
                        "required": ["product_id"],
                    },
                },
            },
        ]

    def dispatch(self, name: str, arguments: dict) -> object:
        if name == "search_catalog":
            return self.search_catalog(**arguments)
        if name == "get_product":
            return self.get_product(**arguments)
        raise ValueError(f"unknown tool: {name}")
