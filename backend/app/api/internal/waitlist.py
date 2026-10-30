"""Internal API endpoints for onboarding and admin."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["internal"])


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


@router.post("/waitlist", response_model=WaitlistResponse)
async def add_to_waitlist(request: WaitlistRequest) -> WaitlistResponse:
    """Add a seller's WhatsApp number to the waitlist.

    When WhatsApp becomes available, we'll send them a message
    with a one-tap connect link.
    """
    # TODO: Implement actual database storage
    # For now, just return success
    return WaitlistResponse(
        message="You'll be notified on WhatsApp when it's ready!",
        phone_number=request.phone_number,
    )


@router.post("/waitlist/notify", response_model=WaitlistNotifyResponse, status_code=501)
async def notify_waitlist(request: WaitlistNotifyRequest) -> WaitlistNotifyResponse:
    """Send WhatsApp notification to a waitlist entry (NOT IMPLEMENTED).

    This will be implemented when WhatsApp unblocks. For now, returns 501.
    """
    return WaitlistNotifyResponse(
        message="Not implemented yet. WhatsApp is still blocked.",
        phone_number=request.phone_number,
    )
