import logging

import stripe
from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.rate_limit import limiter
from app.schemas.stripe import CheckoutSessionRequest, CheckoutSessionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stripe", tags=["stripe"])

stripe.api_key = settings.STRIPE_API_KEY


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
@limiter.limit("10/minute")
async def create_checkout_session(request: Request, data: CheckoutSessionRequest):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Buy King Tide Alerts a coffee",
                            "description": "Support the King Tide Alerts service",
                        },
                        "unit_amount": data.amount,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{settings.APP_URL}/thanks",
            cancel_url=settings.APP_URL,
        )
        if not session.url:
            raise HTTPException(status_code=500, detail="Failed to create checkout URL")
        return CheckoutSessionResponse(checkout_url=session.url)
    except stripe.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail="Failed to create checkout session")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Signature is verified above. Everything after this point is bookkeeping,
    # so it must never fail the request: a non-2xx makes Stripe retry for days.
    try:
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            # Stripe objects support item access but are not dicts (no .get()).
            amount_cents = session["amount_total"] or 0
            logger.info(f"Payment received: {amount_cents / 100:.2f} USD")
    except Exception as e:
        logger.error(f"Stripe webhook handled but not recorded ({event['type']}): {e}")

    return {"status": "ok"}
