"""Seller wallet save and live crypto demo (RPC mocked)."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.echo_store import MemoryEchoStore
from app.main import create_app
from app.payments.crypto.rpc import CryptoRpc
from app.payments.crypto.verify import ChainView, Transfer

DEMO_WALLET = "0x89d53C4A47989D4beA4a9C5972Bcca71E56012C1"
TOKEN = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
BUYER = "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359"
REAL_HASH = "0x" + "ab" * 32
AMOUNT = 15_000_000
ORDER_AT = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)


class FakeRpc(CryptoRpc):
    def __init__(self) -> None:
        super().__init__("http://crypto.test")
        self.calls: list[str] = []

    async def load(self, tx_hash: str) -> ChainView:
        self.calls.append(tx_hash)
        if tx_hash == REAL_HASH:
            return ChainView(
                receipt_found=True,
                status_success=True,
                block_number=100,
                block_timestamp=ORDER_AT + timedelta(minutes=5),
                latest_block=120,
                chain_id=84532,
                transfers=[
                    Transfer(
                        token=TOKEN,
                        sender=BUYER,
                        recipient=DEMO_WALLET,
                        amount=AMOUNT,
                    )
                ],
            )
        return ChainView(
            receipt_found=False,
            chain_id=84532,
            latest_block=120,
        )


def _client(**overrides: object) -> tuple[TestClient, MemoryEchoStore, FakeRpc]:
    store = MemoryEchoStore()
    rpc = FakeRpc()
    values = {
        "llm_provider": "groq",
        "crypto_network": "base-sepolia",
        "crypto_rpc_url": "http://crypto.test",
        "crypto_chain_id": 84532,
        "crypto_token_contract": TOKEN,
        "crypto_min_confirmations": 3,
        "crypto_explorer_url": "https://sepolia.basescan.org",
        "instagram_account_id": "ig-shop",
        "demo_real_tx_hash": "",
    }
    values.update(overrides)
    settings = Settings(**values)
    app = create_app(settings, store=store)
    app.state.crypto_rpc = rpc
    return TestClient(app), store, rpc


def test_wallet_requires_checksum() -> None:
    client, _, _ = _client()
    response = client.post(
        "/api/sellers/crypto-wallet",
        json={"address": DEMO_WALLET.lower()},
    )
    assert response.status_code == 422


def test_wallet_saves_demo_seller() -> None:
    client, store, _ = _client()
    response = client.post("/api/sellers/crypto-wallet", json={"address": DEMO_WALLET})
    assert response.status_code == 200
    assert response.json() == {"address": DEMO_WALLET, "network": "base-sepolia"}
    seller_id = store.ensure_seller("ig-shop", channel="instagram")
    assert store.get_seller(seller_id)["crypto_wallet"] == DEMO_WALLET


def test_demo_reports_missing_hash() -> None:
    client, _, _ = _client(demo_real_tx_hash="")
    response = client.get("/api/demo/crypto")
    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is False
    assert "DEMO_REAL_TX_HASH is not set" in body["message"]
    assert body["cases"] is None


def test_demo_live_cases_with_mocked_rpc() -> None:
    client, store, rpc = _client(demo_real_tx_hash=REAL_HASH)
    store.ensure_seller("ig-shop", channel="instagram")
    # Leave wallet unset so the demo registers DEMO_SELLER_WALLET.
    response = client.get("/api/demo/crypto")
    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["cases"] is not None
    assert len(body["cases"]) == 3
    by_label = {case["label"]: case for case in body["cases"]}
    assert by_label["real"]["verdict"] == "CONFIRMED"
    assert by_label["real"]["amount_usdc"] == "15 USDC"
    assert by_label["real"]["to_address"] == DEMO_WALLET
    assert by_label["real"]["explorer_url"].endswith(REAL_HASH)
    assert by_label["reused"]["verdict"] == "SUSPICIOUS"
    assert by_label["reused"]["reason"] == "reused_hash"
    assert by_label["fake"]["verdict"] == "SUSPICIOUS"
    assert by_label["fake"]["reason"] == "missing_tx"
    assert by_label["fake"]["tx_hash"] != REAL_HASH
    assert REAL_HASH in rpc.calls
