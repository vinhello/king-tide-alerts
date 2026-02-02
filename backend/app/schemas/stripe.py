from pydantic import BaseModel


class CheckoutSessionRequest(BaseModel):
    amount: int = 500  # cents, default $5


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
