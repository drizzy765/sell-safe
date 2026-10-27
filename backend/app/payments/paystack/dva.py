"""Paystack dedicated virtual account client."""

from typing import Any

import httpx

from app.config import Settings

_BASE_URL = "https://api.paystack.co"


class PaystackClient:
    """Verify Paystack transactions before trusting webhook payloads."""

    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    def _headers(self) -> dict[str, str]:
        key = self._settings.paystack_secret_key
        if not key:
            raise RuntimeError("PAYSTACK_SECRET_KEY is not set")
        return {"Authorization": f"Bearer {key}"}

    async def verify_transaction(self, transaction_id: int | str) -> dict[str, Any]:
        url = f"{_BASE_URL}/transaction/verify/{transaction_id}"
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.get(url, headers=self._headers())
            response.raise_for_status()
        body = response.json()
        if not body.get("status"):
            raise RuntimeError(f"Paystack verify failed: {body.get('message')}")
        return body.get("data", {})
