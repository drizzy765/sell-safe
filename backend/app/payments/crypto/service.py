"""Load a receipt, judge it, and store the hash once."""

from datetime import datetime

from app.payments.crypto.checkout import expected_usdc_base
from app.payments.crypto.rpc import CryptoRpc
from app.payments.crypto.store import CryptoPaymentStore
from app.payments.crypto.verify import CryptoCheck, judge


async def verify_tx(
    *,
    tx_hash: str,
    order: dict,
    seller_wallet: str,
    token_contract: str,
    min_confirmations: int,
    chain_id: int,
    network: str,
    rpc: CryptoRpc | None,
    store: CryptoPaymentStore,
    order_created_at: datetime,
    screenshot_only: bool = False,
) -> CryptoCheck:
    expected = expected_usdc_base(order)
    existing = store.get(tx_hash)
    already_used = False
    if existing is not None:
        already_used = existing["order_id"] != order["id"] or existing["status"] == "CONFIRMED"
    if screenshot_only or already_used or expected is None or rpc is None or not token_contract:
        reason = "screenshot_only"
        if already_used:
            reason = "reused_hash"
        elif expected is None:
            reason = "amount_not_set"
        elif not token_contract or rpc is None:
            reason = "rpc_not_configured"
        result = CryptoCheck(status="SUSPICIOUS", reason=reason)
    else:
        view = await rpc.load(tx_hash)
        result = judge(
            view,
            seller_wallet=seller_wallet,
            token_contract=token_contract,
            expected_amount=expected,
            min_confirmations=min_confirmations,
            order_created_at=order_created_at,
            expected_chain_id=chain_id,
            already_used=False,
            screenshot_only=False,
        )
    if not already_used:
        store.save(
            {
                "order_id": order["id"],
                "tx_hash": tx_hash,
                "network": network,
                "from_address": result.sender,
                "to_address": result.recipient or seller_wallet,
                "amount": result.amount,
                "confirmations": result.confirmations,
                "status": result.status,
                "reason": result.reason,
            }
        )
    return result
