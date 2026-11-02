"""Order tools. create_order writes an awaiting_payment row."""

from __future__ import annotations

from app.db.orders import OrderStore


class OrderTools:
    """Tools bound to a seller and buyer."""

    def __init__(
        self,
        seller_id: str,
        buyer_id: str,
        orders: OrderStore,
        *,
        crypto_wallet: str = "",
        crypto_network: str = "base-sepolia",
        bank_name: str = "",
        account_name: str = "",
        account_number: str = "",
    ) -> None:
        self._seller_id = seller_id
        self._buyer_id = buyer_id
        self._orders = orders
        self._crypto_wallet = crypto_wallet
        self._crypto_network = crypto_network
        self._bank_name = (bank_name or "").strip()
        self._account_name = (account_name or "").strip()
        self._account_number = "".join(ch for ch in (account_number or "") if ch.isdigit())

    def payment_details(self) -> dict:
        """Return Naira bank transfer details for this shop (or configured=false)."""
        if not self._account_number or not self._account_name:
            return {
                "configured": False,
                "message": (
                    "This shop has not added bank transfer details yet. "
                    "Ask the buyer to wait while the seller adds account name, "
                    "bank, and account number in Sell-Safe onboarding."
                ),
            }
        return {
            "configured": True,
            "bank_name": self._bank_name or "Bank transfer",
            "account_name": self._account_name,
            "account_number": self._account_number,
            "message": (
                f"Transfer to {self._account_name} / {self._bank_name or 'bank'} "
                f"/ {self._account_number}. After paying, send the receipt photo."
            ),
        }

    def create_order(self, *, items: list[dict]) -> dict:
        """Create an order from a list of {product_id, qty} items."""
        total_kobo = sum(int(item["qty"]) * int(item["unit_price_kobo"]) for item in items)
        order = self._orders.create_order(
            seller_id=self._seller_id,
            buyer_id=self._buyer_id,
            items=items,
            total_kobo=total_kobo,
        )
        from app.payments.crypto.handle import crypto_instructions_for_items

        usdc_base, instructions = crypto_instructions_for_items(
            items,
            wallet=self._crypto_wallet,
            network=self._crypto_network,
            ref=str(order["ref"]),
        )
        if usdc_base is not None and instructions is not None:
            order["expected_usdc_base"] = usdc_base
            order["crypto_instructions"] = instructions
        payout = self.payment_details()
        order["payment_details"] = payout
        return order

    def get_order_status(self, *, order_ref: str) -> dict | None:
        """Get the status of an order by its reference."""
        return self._orders.get_order_by_ref(order_ref)

    def cancel_order(self, *, order_ref: str) -> dict | None:
        """Cancel an order by reference."""
        return self._orders.cancel_order(order_ref)

    def schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_order",
                    "description": (
                        "Create an order from items. "
                        "Each item must include product_id, qty, and unit_price_kobo. "
                        "Response includes payment_details for bank transfer when configured."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "product_id": {"type": "string"},
                                        "qty": {"type": "integer"},
                                        "unit_price_kobo": {"type": "integer"},
                                    },
                                    "required": ["product_id", "qty", "unit_price_kobo"],
                                },
                            },
                        },
                        "required": ["items"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_payment_details",
                    "description": (
                        "Get the shop bank transfer details (account name, bank, account number). "
                        "Call this when the buyer asks for account number / how to pay."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_order_status",
                    "description": "Get the status of an order by reference.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_ref": {"type": "string"},
                        },
                        "required": ["order_ref"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_order",
                    "description": "Cancel an order by reference.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_ref": {"type": "string"},
                        },
                        "required": ["order_ref"],
                    },
                },
            },
        ]

    def dispatch(self, name: str, arguments: dict) -> object:
        if name == "create_order":
            return self.create_order(**arguments)
        if name == "get_payment_details":
            return self.payment_details()
        if name == "get_order_status":
            return self.get_order_status(**arguments)
        if name == "cancel_order":
            return self.cancel_order(**arguments)
        raise ValueError(f"unknown tool: {name}")
