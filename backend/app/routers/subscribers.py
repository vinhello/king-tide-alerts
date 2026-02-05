import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.king_tide_event import KingTideEvent
from app.models.subscriber import Subscriber
from app.schemas.subscriber import (
    ConfirmResponse,
    SubscribeRequest,
    SubscriberResponse,
    UnsubscribeResponse,
)
from app.services.notification import send_confirmation, send_king_tide_alert

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


@router.post("/admin/test-alert")
async def test_alert(
    height: float = 6.8,
    days_until: int = 7,
    db: Session = Depends(get_db),
    x_api_key: str = Header(...),
):
    if not settings.ADMIN_API_KEY or x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    """Send a test alert to all confirmed subscribers.

    Query params:
        height: predicted tide height in ft (default 6.8, king tide).
                Use e.g. 6.2 for a non-king-tide high-tide alert.
        days_until: simulated days until the event (default 7).
    """
    subscribers = (
        db.query(Subscriber).filter(Subscriber.confirmed.is_(True)).all()
    )
    if not subscribers:
        raise HTTPException(status_code=404, detail="No confirmed subscribers found")

    event_dt = datetime.now(timezone.utc) + timedelta(days=days_until)
    event = KingTideEvent(
        event_datetime=event_dt,
        predicted_height=height,
        station_id=settings.NOAA_STATION_ID,
    )
    db.add(event)
    db.commit()

    notified = 0
    for subscriber in subscribers:
        await send_king_tide_alert(
            subscriber=subscriber,
            event_datetime=event.event_datetime,
            height=event.predicted_height,
            days_until=days_until,
        )
        notified += 1

    return {"message": f"Test alert sent to {notified} subscriber(s)"}
