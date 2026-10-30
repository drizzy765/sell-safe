"""Top-level harness: one inbound turn -> outbound reply."""

from app.agent.graph.nodes import observe, respond, route, sales_agent
from app.agent.graph.seller_cmd import seller_command_agent
from app.agent.graph.state import State
from app.agent.graph.verify import verify_payment_turn
from app.agent.tools.catalog import CatalogTools
from app.agent.tools.orders import OrderTools
from app.channels.base import ChannelAdapter, InboundMessage
from app.db.catalog_store import CatalogStore
from app.db.echo_store import EchoStore
from app.db.fraud_store import FraudStore
from app.db.orders import OrderStore
from app.db.payments import PaymentStore
from app.decisions.base import JevClient
from app.llm.base import LLMProvider


async def run_turn(
    message: InboundMessage,
    *,
    seller_id: str,
    buyer_id: str,
    channel_adapter: ChannelAdapter,
    store: EchoStore,
    jev: JevClient,
    provider: LLMProvider,
    catalog_store: CatalogStore,
    order_store: OrderStore,
    payment_store: PaymentStore | None = None,
    fraud_store: FraudStore | None = None,
    pii_salt: str = "",
    business_name: str | None = None,
) -> State:
    """Run one inbound turn through the agent graph."""
    state = State(
        trace_id=f"{message.external_id}-{seller_id}",
        channel=message.channel,
        seller_id=seller_id,
        buyer_id=buyer_id,
        buyer_external_id=message.sender_id,
        message=message,
    )

    state = observe(state, store)
    seller_language = store.get_seller_language(seller_id)
    state = await route(state, jev, seller_language)

    catalog_tools = CatalogTools(seller_id, catalog_store)
    seller = store.get_seller(seller_id) or {}
    order_tools = OrderTools(
        seller_id,
        buyer_id,
        order_store,
        crypto_wallet=str(seller.get("crypto_wallet") or ""),
        crypto_network=str(seller.get("crypto_network") or "base-sepolia"),
    )

    if state.intent in ("price_question", "order", "chit_chat"):
        state = await sales_agent(state, provider, catalog_tools, order_tools, business_name)
    elif state.intent == "payment_proof":
        if payment_store is None:
            state.reply = fallback_for_language(state.language, "payment_check")
        else:
            verify_result = await verify_payment_turn(
                message,
                seller_id=seller_id,
                buyer_id=buyer_id,
                channel_adapter=channel_adapter,
                store=store,
                order_store=order_store,
                payment_store=payment_store,
                provider=provider,
                jev=jev,
                pii_salt=pii_salt,
                fraud_store=fraud_store,
            )
            state.reply = verify_result.verdict.verdict
            state.verdict = verify_result.verdict.model_dump()
    elif state.intent == "complaint":
        state.reply = fallback_for_language(state.language, "escalate")
    elif state.intent == "seller_command":
        if payment_store is None:
            state.reply = fallback_for_language(state.language, "seller_command")
        else:
            state.reply = await seller_command_agent(
                message.text or "",
                seller_id=seller_id,
                buyer_id=buyer_id,
                sender_id=message.sender_id,
                channel_adapter=channel_adapter,
                store=store,
                order_store=order_store,
                payment_store=payment_store,
                fraud_store=fraud_store,
                pii_salt=pii_salt,
            )
    elif state.intent == "order_status":
        state.reply = fallback_for_language(state.language, "order_status")
    else:
        state.reply = fallback_for_language(state.language, "unknown")

    state = await respond(state, channel_adapter, message.sender_id, store)
    return state


def fallback_for_language(language: str, kind: str) -> str:
    maps = {
        "en": {
            "payment_check": "I will check this payment and get back to you.",
            "escalate": "I have passed this to the seller.",
            "seller_command": "Seller commands are not available yet.",
            "order_status": "Please send the order reference to check status.",
            "unknown": "I'm not sure I understand. Can you rephrase?",
        },
        "pcm": {
            "payment_check": "I go check this payment come back.",
            "escalate": "I don send am to the seller.",
            "seller_command": "Seller command no dey yet.",
            "order_status": "Send the order ref make I check am.",
            "unknown": "I no too understand. Abeg talk am again.",
        },
        "yo": {
            "payment_check": "N ṣe ayẹ̀wò owo yìí, n óò padà.",
            "escalate": "Mo ti fi ránṣẹ́ sí onísò.",
            "seller_command": "Àṣẹ onísò kò sí láàárín.",
            "order_status": "Jọ̀wọ́ ránṣẹ́ nọ́mba àṣẹ láti ṣe ayẹ̀wò rẹ̀.",
            "unknown": "N ko gbọ́ dáadáa. Ṣé o lè sọ rẹ̀ padà?",
        },
    }
    return maps.get(language, maps["en"]).get(kind, maps["en"]["unknown"])
