"""Harness state per inbound turn."""

from pydantic import BaseModel, Field

from app.channels.base import InboundMessage


class Turn(BaseModel):
    role: str
    content: str


class State(BaseModel):
    trace_id: str
    channel: str
    seller_id: str
    buyer_id: str
    buyer_external_id: str
    message: InboundMessage
    language: str = "en"
    intent: str = "chit_chat"
    route_scores: dict = Field(default_factory=dict)
    history: list[Turn] = Field(default_factory=list)
    order: dict | None = None
    tool_calls: list[dict] = Field(default_factory=list)
    extraction: dict | None = None
    verdict: dict | None = None
    reply: str = ""
    steps: int = 0
    errors: list[str] = Field(default_factory=list)

    def bump(self) -> "State":
        self.steps += 1
        return self
