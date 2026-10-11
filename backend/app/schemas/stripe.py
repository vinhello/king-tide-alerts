from pydantic import BaseModel, Field

from app.config import settings


class CheckoutSessionRequest(BaseModel):
    amount: int = Field(
        default=500,
        ge=settings.DONATION_MIN_CENTS,
        le=settings.DONATION_MAX_CENTS,
        description="Donation amount in cents",
    )


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
