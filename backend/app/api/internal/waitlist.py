"""Public WhatsApp waitlist and the not-yet-implemented notify stub."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.db.waitlist_store import (
    DuplicateWaitlistError,
    MemoryWaitlistStore,
    WaitlistStore,
    build_waitlist_store,
)

router = APIRouter(prefix="/api", tags=["internal"])

WAITLIST_MESSAGE = "We'll message you on WhatsApp when ready"


class WaitlistRequest(BaseModel):
    """WhatsApp waitlist signup request."""

    phone_number: str = Field(
        ...,
        description="Nigerian WhatsApp number in international format (+234XXXXXXXXXX)",
        pattern=r"^\+234[0-9]{10}$",
        examples=["+2348012345678"],
    )


class WaitlistResponse(BaseModel):
    """WhatsApp waitlist signup response."""

    message: str
    phone_number: str


class WaitlistNotifyRequest(BaseModel):
    """Request to notify a waitlist entry (admin only, stub for now)."""

    phone_number: str


class WaitlistNotifyResponse(BaseModel):
    """Response from notify endpoint."""

    message: str
    phone_number: str


def _supabase_ready(settings: object) -> bool:
    return bool(
        getattr(settings, "supabase_url", "") and getattr(settings, "supabase_service_role_key", "")
    )


def _waitlist(request: Request) -> WaitlistStore:
    current = request.app.state.waitlist
    if current is None:
        settings = request.app.state.settings
        if _supabase_ready(settings):
            current = build_waitlist_store(settings)
        else:
            current = MemoryWaitlistStore()
        request.app.state.waitlist = current
    return current


@router.post("/waitlist", response_model=WaitlistResponse, status_code=201)
async def add_to_waitlist(body: WaitlistRequest, request: Request) -> WaitlistResponse:
    """Store a seller's WhatsApp number. Public: no internal token."""
    try:
        _waitlist(request).add(body.phone_number)
    except DuplicateWaitlistError:
        raise HTTPException(
            status_code=409,
            detail="This number is already on the waitlist.",
        ) from None
    return WaitlistResponse(message=WAITLIST_MESSAGE, phone_number=body.phone_number)


@router.post("/waitlist/notify", response_model=WaitlistNotifyResponse, status_code=501)
async def notify_waitlist(body: WaitlistNotifyRequest) -> WaitlistNotifyResponse:
    """Send a WhatsApp notification (not implemented).

    This stays a stub until WhatsApp unblocks. It does not send a message.
    """
    return WaitlistNotifyResponse(
        message="Not implemented yet. WhatsApp is still blocked.",
        phone_number=body.phone_number,
    )
