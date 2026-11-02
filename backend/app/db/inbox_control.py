"""Per-chat takeover, reply-mode overrides, and AI draft replies (hackathon memory)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


@dataclass
class ConversationControl:
    seller_id: str
    buyer_id: str
    paused: bool = False
    reply_mode: str | None = None  # None → use shop global
    folder: str = "primary"  # primary | general | requests
    unread: int = 0
    last_inbound_at: str | None = None

    def public_dict(self) -> dict:
        return asdict(self)


@dataclass
class DraftReply:
    id: str
    seller_id: str
    buyer_id: str
    buyer_external_id: str
    channel: str
    customer_text: str
    draft_text: str
    mode: str
    status: str = "pending"  # pending | sent | rejected | edited
    product: dict | None = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    approver: str | None = None

    def public_dict(self) -> dict:
        return asdict(self)


class InboxControlStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._controls: dict[tuple[str, str], ConversationControl] = {}
        self._drafts: dict[str, DraftReply] = {}
        self._demo_mode_by_seller: dict[str, bool] = {}

    def get_control(self, seller_id: str, buyer_id: str) -> ConversationControl:
        key = (seller_id, buyer_id)
        with self._lock:
            row = self._controls.get(key)
            if row is None:
                row = ConversationControl(seller_id=seller_id, buyer_id=buyer_id)
                self._controls[key] = row
            return deepcopy(row)

    def set_paused(self, seller_id: str, buyer_id: str, paused: bool) -> ConversationControl:
        with self._lock:
            row = self._controls.setdefault(
                (seller_id, buyer_id),
                ConversationControl(seller_id=seller_id, buyer_id=buyer_id),
            )
            row.paused = paused
            return deepcopy(row)

    def set_reply_mode(
        self, seller_id: str, buyer_id: str, mode: str | None
    ) -> ConversationControl:
        with self._lock:
            row = self._controls.setdefault(
                (seller_id, buyer_id),
                ConversationControl(seller_id=seller_id, buyer_id=buyer_id),
            )
            row.reply_mode = mode
            return deepcopy(row)

    def mark_inbound(self, seller_id: str, buyer_id: str, *, at: str | None = None) -> None:
        with self._lock:
            row = self._controls.setdefault(
                (seller_id, buyer_id),
                ConversationControl(seller_id=seller_id, buyer_id=buyer_id),
            )
            row.unread += 1
            row.last_inbound_at = at or _now()

    def clear_unread(self, seller_id: str, buyer_id: str) -> None:
        with self._lock:
            row = self._controls.get((seller_id, buyer_id))
            if row is not None:
                row.unread = 0

    def save_draft(self, draft: DraftReply) -> DraftReply:
        with self._lock:
            self._drafts[draft.id] = deepcopy(draft)
            return deepcopy(draft)

    def get_draft(self, draft_id: str) -> DraftReply | None:
        with self._lock:
            row = self._drafts.get(draft_id)
            return deepcopy(row) if row else None

    def list_drafts(
        self, seller_id: str, *, buyer_id: str | None = None, status: str = "pending"
    ) -> list[DraftReply]:
        with self._lock:
            rows = [
                deepcopy(d)
                for d in self._drafts.values()
                if d.seller_id == seller_id
                and (buyer_id is None or d.buyer_id == buyer_id)
                and (status == "*" or d.status == status)
            ]
        rows.sort(key=lambda d: d.created_at, reverse=True)
        return rows

    def update_draft(
        self,
        draft_id: str,
        *,
        status: str | None = None,
        draft_text: str | None = None,
        approver: str | None = None,
    ) -> DraftReply | None:
        with self._lock:
            row = self._drafts.get(draft_id)
            if row is None:
                return None
            if status is not None:
                row.status = status
            if draft_text is not None:
                row.draft_text = draft_text
            if approver is not None:
                row.approver = approver
            row.updated_at = _now()
            return deepcopy(row)

    @staticmethod
    def new_draft_id() -> str:
        return str(uuid4())

    def get_demo_mode(self, seller_id: str) -> bool:
        with self._lock:
            return bool(self._demo_mode_by_seller.get(seller_id, False))

    def set_demo_mode(self, seller_id: str, enabled: bool) -> bool:
        with self._lock:
            self._demo_mode_by_seller[seller_id] = bool(enabled)
            return bool(enabled)

    def create_reply_draft(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        buyer_external_id: str,
        channel: str,
        customer_text: str,
        draft_text: str,
        mode: str,
        product: dict | None = None,
    ) -> DraftReply:
        draft = DraftReply(
            id=self.new_draft_id(),
            seller_id=seller_id,
            buyer_id=buyer_id,
            buyer_external_id=buyer_external_id,
            channel=channel,
            customer_text=customer_text,
            draft_text=draft_text,
            mode=mode,
            product=product,
        )
        return self.save_draft(draft)
