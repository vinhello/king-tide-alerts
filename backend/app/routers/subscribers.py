import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.rate_limit import limiter
from app.models.subscriber import Subscriber
from app.schemas.subscriber import (
    ConfirmResponse,
    ResendConfirmationRequest,
    ResendConfirmationResponse,
    SubscribeRequest,
    SubscriberResponse,
    UnsubscribeResponse,
)
from app.services.notification import send_confirmation

router = APIRouter(prefix="/api", tags=["subscribers"])

# Both endpoints can cause an email to someone else's inbox, so they are
# limited per client and, for resend, by a shared cap as a backstop.
SUBSCRIBE_LIMIT = "5/hour"
RESEND_PER_CLIENT_LIMIT = "3/hour"
RESEND_GLOBAL_LIMIT = "30/hour"
RESEND_MESSAGE = (
    "If that address is subscribed and not yet confirmed, "
    "a new confirmation email is on its way."
)


def _global_key(request: Request) -> str:
    return "resend-global"


@router.post("/subscribe", response_model=SubscriberResponse, status_code=201)
@limiter.limit(SUBSCRIBE_LIMIT)
async def subscribe(
    request: Request,
    data: SubscribeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Check for duplicate email
    if data.email:
        existing = db.query(Subscriber).filter(Subscriber.email == data.email).first()
        if existing:
            if existing.unsubscribed_at is not None:
                # Came back after unsubscribing: reactivate the same record as a
                # fresh, unconfirmed signup and record where it came from.
                existing.unsubscribed_at = None
                existing.confirmed = False
                existing.confirmed_at = None
                existing.name = data.name
                existing.notification_preference = data.notification_preference
                _apply_signup_source(existing, data)
                db.commit()
                db.refresh(existing)
                background_tasks.add_task(send_confirmation, existing)
                return existing
            if existing.confirmed:
                raise HTTPException(status_code=400, detail="Email already subscribed")
            # Signed up before but never confirmed: resend rather than dead-end.
            background_tasks.add_task(send_confirmation, existing)
            return existing

    # Check for duplicate phone
    if data.phone:
        existing = db.query(Subscriber).filter(Subscriber.phone == data.phone).first()
        if existing:
            raise HTTPException(
                status_code=400, detail="Phone number already subscribed"
            )

    subscriber = Subscriber(
        name=data.name,
        email=data.email,
        phone=data.phone,
        notification_preference=data.notification_preference,
        unsubscribe_token=secrets.token_urlsafe(32),
        confirmed=False,
    )
    _apply_signup_source(subscriber, data)
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)

    background_tasks.add_task(send_confirmation, subscriber)

    return subscriber


@router.get("/confirm/{token}", response_model=ConfirmResponse)
async def confirm_subscription(token: str, db: Session = Depends(get_db)):
    subscriber = (
        db.query(Subscriber).filter(Subscriber.unsubscribe_token == token).first()
    )
    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid confirmation token")
    if subscriber.unsubscribed_at is not None:
        # An old confirmation link must not silently reactivate someone who
        # unsubscribed. They can sign up again from the site.
        raise HTTPException(
            status_code=410, detail="This subscription was cancelled. Sign up again to restart it."
        )

    subscriber.confirmed = True
    if subscriber.confirmed_at is None:
        subscriber.confirmed_at = datetime.now(timezone.utc)
    db.commit()

    return ConfirmResponse(
        message="Subscription confirmed! You'll receive king tide alerts."
    )


@router.get("/unsubscribe/{token}", response_model=UnsubscribeResponse)
async def unsubscribe(token: str, db: Session = Depends(get_db)):
    subscriber = (
        db.query(Subscriber).filter(Subscriber.unsubscribe_token == token).first()
    )
    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid unsubscribe token")

    # Keep the row: churn stays measurable and a later signup reactivates it.
    if subscriber.unsubscribed_at is None:
        subscriber.unsubscribed_at = datetime.now(timezone.utc)
        db.commit()

    return UnsubscribeResponse(
        message="You've been unsubscribed from King Tide Alerts."
    )


@router.post("/resend-confirmation", response_model=ResendConfirmationResponse)
@limiter.limit(RESEND_PER_CLIENT_LIMIT)
@limiter.limit(RESEND_GLOBAL_LIMIT, key_func=_global_key)
async def resend_confirmation(
    request: Request,
    data: ResendConfirmationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Resend the confirmation email to an unconfirmed signup.

    The response is the same whether or not the address is known, so this
    cannot be used to find out who is subscribed.
    """
    subscriber = (
        db.query(Subscriber).filter(Subscriber.email == str(data.email)).first()
    )
    if (
        subscriber is not None
        and not subscriber.confirmed
        and subscriber.unsubscribed_at is None
    ):
        background_tasks.add_task(send_confirmation, subscriber)
    return ResendConfirmationResponse(message=RESEND_MESSAGE)


def _apply_signup_source(subscriber: Subscriber, data: SubscribeRequest) -> None:
    subscriber.signup_referrer = data.signup_referrer
    subscriber.signup_utm_source = data.signup_utm_source
    subscriber.signup_utm_medium = data.signup_utm_medium
    subscriber.signup_utm_campaign = data.signup_utm_campaign
    subscriber.signup_landing_path = data.signup_landing_path
