import secrets

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.subscriber import Subscriber
from app.schemas.subscriber import (
    ConfirmResponse,
    SubscribeRequest,
    SubscriberResponse,
    UnsubscribeResponse,
)
from app.services.notification import send_confirmation

router = APIRouter(prefix="/api", tags=["subscribers"])


@router.post("/subscribe", response_model=SubscriberResponse, status_code=201)
async def subscribe(
    data: SubscribeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Check for duplicate email
    if data.email:
        existing = (
            db.query(Subscriber).filter(Subscriber.email == data.email).first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email already subscribed")

    # Check for duplicate phone
    if data.phone:
        existing = (
            db.query(Subscriber).filter(Subscriber.phone == data.phone).first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Phone number already subscribed")

    subscriber = Subscriber(
        name=data.name,
        email=data.email,
        phone=data.phone,
        notification_preference=data.notification_preference,
        unsubscribe_token=secrets.token_urlsafe(32),
        confirmed=False,
    )
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)

    background_tasks.add_task(send_confirmation, subscriber)

    return subscriber


@router.get("/confirm/{token}", response_model=ConfirmResponse)
async def confirm_subscription(token: str, db: Session = Depends(get_db)):
    subscriber = (
        db.query(Subscriber)
        .filter(Subscriber.unsubscribe_token == token)
        .first()
    )
    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid confirmation token")

    subscriber.confirmed = True
    db.commit()

    return ConfirmResponse(message="Subscription confirmed! You'll receive king tide alerts.")


@router.get("/unsubscribe/{token}", response_model=UnsubscribeResponse)
async def unsubscribe(token: str, db: Session = Depends(get_db)):
    subscriber = (
        db.query(Subscriber)
        .filter(Subscriber.unsubscribe_token == token)
        .first()
    )
    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid unsubscribe token")

    db.delete(subscriber)
    db.commit()

    return UnsubscribeResponse(message="You've been unsubscribed from King Tide Alerts.")
