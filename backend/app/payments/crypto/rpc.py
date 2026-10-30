"""JSON-RPC reads for one transaction. No provider SDK."""

from datetime import UTC, datetime
from typing import Any

import httpx

from app.payments.crypto.verify import ChainView, Transfer, decode_transfer_logs

# ERC-20 selectors
_DECIMALS = "0x313ce567"
_SYMBOL = "0x95d89b41"


class RpcError(RuntimeError):
    """The node rejected the call or returned an error object."""


def _quantity(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"", "0x"}:
        return None
    return int(text, 16)


def _decode_string(data: str) -> str:
    """Decode a Solidity string or bytes32 ABI return."""
    raw = data.removeprefix("0x")
    if not raw:
        return ""
    blob = bytes.fromhex(raw)
    # dynamic string: offset + length + bytes
    if len(blob) >= 96:
        length = int.from_bytes(blob[32:64], "big")
        return blob[64 : 64 + length].decode("utf-8", errors="replace")
    # bytes32 symbol
    return blob.rstrip(b"\x00").decode("utf-8", errors="replace")


class CryptoRpc:
    def __init__(self, rpc_url: str, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._rpc_url = rpc_url
        self._transport = transport

    async def _call(self, method: str, params: list[Any]) -> Any:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        async with httpx.AsyncClient(transport=self._transport, timeout=20.0) as client:
            response = await client.post(self._rpc_url, json=payload)
            response.raise_for_status()
            body = response.json()
        if body.get("error"):
            raise RpcError(str(body["error"].get("message") or "rpc error"))
        return body.get("result")

    async def probe(self, token_contract: str) -> dict[str, Any]:
        """Chain id, latest block, and ERC-20 symbol/decimals for env checks."""
        chain_id = _quantity(await self._call("eth_chainId", []))
        latest = _quantity(await self._call("eth_blockNumber", []))
        # eth_call accepts any EIP-55 form; lowercase avoids some node quirks.
        token = token_contract.lower()
        decimals_raw = await self._call(
            "eth_call",
            [{"to": token, "data": _DECIMALS}, "latest"],
        )
        symbol_raw = await self._call(
            "eth_call",
            [{"to": token, "data": _SYMBOL}, "latest"],
        )
        decimals = _quantity(str(decimals_raw)) if decimals_raw else None
        symbol = _decode_string(str(symbol_raw or "0x")) if symbol_raw not in (None, "0x") else ""
        return {
            "chain_id": chain_id,
            "latest_block": latest,
            "token": token_contract,
            "symbol": symbol,
            "decimals": decimals,
            "token_call_ok": decimals is not None and bool(symbol),
        }

    async def load(self, tx_hash: str) -> ChainView:
        receipt = await self._call("eth_getTransactionReceipt", [tx_hash])
        chain_id = _quantity(await self._call("eth_chainId", []))
        latest = _quantity(await self._call("eth_blockNumber", []))
        if not isinstance(receipt, dict):
            return ChainView(receipt_found=False, chain_id=chain_id, latest_block=latest)
        block_number = _quantity(receipt.get("blockNumber"))
        timestamp = None
        if block_number is not None:
            block = await self._call("eth_getBlockByNumber", [receipt["blockNumber"], False])
            if isinstance(block, dict):
                seconds = _quantity(block.get("timestamp"))
                if seconds is not None:
                    timestamp = datetime.fromtimestamp(seconds, UTC)
        logs = receipt.get("logs") or []
        transfers: list[Transfer] = decode_transfer_logs(logs) if isinstance(logs, list) else []
        return ChainView(
            receipt_found=True,
            status_success=_quantity(receipt.get("status")) == 1,
            block_number=block_number,
            block_timestamp=timestamp,
            latest_block=latest,
            chain_id=chain_id,
            transfers=transfers,
        )
