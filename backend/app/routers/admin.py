import hmac
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.king_tide_event import KingTideEvent
from app.models.notification_sent import NotificationSent, NotificationType
from app.models.subscriber import Subscriber
from app.schemas.admin import (
    AdminEvent,
    DailyCount,
    GrowthPoint,
    NotificationHistoryItem,
    NotificationStats,
    SubscriberStats,
    SystemHealth,
    TestAlertResponse,
)
from app.rate_limit import limiter
from app.services.notification import send_king_tide_alert

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin_auth(
    x_admin_password: str | None = Header(None),
) -> str:
    if not x_admin_password:
        raise HTTPException(status_code=401, detail="Missing authentication header")
    if settings.ADMIN_PASSWORD and hmac.compare_digest(
        x_admin_password, settings.ADMIN_PASSWORD
    ):
        return x_admin_password
    raise HTTPException(status_code=403, detail="Invalid credentials")


@router.get("/health", response_model=SystemHealth)
@limiter.limit("10/minute")
async def admin_health(
    request: Request,
    _key: str = Depends(verify_admin_auth),
    db: Session = Depends(get_db),
):
    from app.services.scheduler import scheduler

    scheduler_running = scheduler.running
    next_run_time = None
    if scheduler_running:
        job = scheduler.get_job("daily_king_tide_check")
        if job and job.next_run_time:
            next_run_time = job.next_run_time.isoformat()

    latest_event = (
        db.query(KingTideEvent).order_by(KingTideEvent.created_at.desc()).first()
    )

    return SystemHealth(
        scheduler_running=scheduler_running,
        next_run_time=next_run_time,
        environment=settings.ENVIRONMENT,
        latest_event_at=latest_event.created_at if latest_event else None,
    )


@router.get("/stats", response_model=SubscriberStats)
@limiter.limit("10/minute")
async def subscriber_stats(
    request: Request,
    _key: str = Depends(verify_admin_auth),
    db: Session = Depends(get_db),
):
    total = db.query(Subscriber).count()
    confirmed = db.query(Subscriber).filter(Subscriber.confirmed.is_(True)).count()
    unconfirmed = total - confirmed

    email_only = (
        db.query(Subscriber)
        .filter(Subscriber.notification_preference == "email")
        .count()
    )
    sms_only = (
        db.query(Subscriber).filter(Subscriber.notification_preference == "sms").count()
    )
    both = (
        db.query(Subscriber)
        .filter(Subscriber.notification_preference == "both")
        .count()
    )

    # 30-day growth
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    rows = (
        db.query(
            func.date(Subscriber.created_at).label("date"),
            func.count().label("count"),
        )
        .filter(Subscriber.created_at >= thirty_days_ago)
        .group_by(func.date(Subscriber.created_at))
        .order_by(func.date(Subscriber.created_at))
        .all()
    )
    growth = [GrowthPoint(date=str(r.date), count=r.count) for r in rows]

    return SubscriberStats(
        total=total,
        confirmed=confirmed,
        unconfirmed=unconfirmed,
        email_only=email_only,
        sms_only=sms_only,
        both=both,
        growth=growth,
    )


@router.get("/notifications", response_model=NotificationStats)
@limiter.limit("10/minute")
async def notification_stats(
    request: Request,
    _key: str = Depends(verify_admin_auth),
    db: Session = Depends(get_db),
):
    total_sent = db.query(NotificationSent).count()

    seven_day = (
        db.query(NotificationSent)
        .filter(NotificationSent.notification_type == NotificationType.SEVEN_DAY_ALERT)
        .count()
    )
    forty_eight = (
        db.query(NotificationSent)
        .filter(
            NotificationSent.notification_type
            == NotificationType.FORTY_EIGHT_HOUR_REMINDER
        )
        .count()
    )
    confirmations = (
        db.query(NotificationSent)
        .filter(NotificationSent.notification_type == NotificationType.CONFIRMATION)
        .count()
    )

    # Last 20 notifications
    recent_rows = (
        db.query(NotificationSent)
        .join(Subscriber)
        .order_by(NotificationSent.sent_at.desc())
        .limit(20)
        .all()
    )
    recent = [
        NotificationHistoryItem(
            id=str(n.id),
            subscriber_name=n.subscriber.name,
            notification_type=n.notification_type.value,
            sent_at=n.sent_at,
        )
        for n in recent_rows
    ]

    # 30-day daily counts
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    daily_rows = (
        db.query(
            func.date(NotificationSent.sent_at).label("date"),
            func.count().label("count"),
        )
        .filter(NotificationSent.sent_at >= thirty_days_ago)
        .group_by(func.date(NotificationSent.sent_at))
        .order_by(func.date(NotificationSent.sent_at))
        .all()
    )
    daily_counts = [DailyCount(date=str(r.date), count=r.count) for r in daily_rows]

    return NotificationStats(
        total_sent=total_sent,
        seven_day_alerts=seven_day,
        forty_eight_hour_reminders=forty_eight,
        confirmations=confirmations,
        recent=recent,
        daily_counts=daily_counts,
    )


@router.get("/events", response_model=list[AdminEvent])
@limiter.limit("10/minute")
async def upcoming_events(
    request: Request,
    _key: str = Depends(verify_admin_auth),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    events = (
        db.query(KingTideEvent)
        .filter(KingTideEvent.event_datetime >= now)
        .order_by(KingTideEvent.event_datetime.asc())
        .all()
    )
    return [
        AdminEvent(
            id=str(e.id),
            event_datetime=e.event_datetime,
            predicted_height=e.predicted_height,
            seven_day_alert_sent=e.seven_day_alert_sent,
            forty_eight_hour_alert_sent=e.forty_eight_hour_alert_sent,
            notifications_sent=len(e.notifications),
        )
        for e in events
    ]


@router.post("/test-alert", response_model=TestAlertResponse)
@limiter.limit("2/minute")
async def test_alert(
    request: Request,
    height: float = Query(default=6.8, ge=5.0, le=20.0),
    days_until: int = Query(default=7, ge=1, le=30),
    _key: str = Depends(verify_admin_auth),
    db: Session = Depends(get_db),
):
    """Send a test alert to all confirmed subscribers.

    Query params:
        height: predicted tide height in ft (default 6.8, king tide).
                Use e.g. 6.2 for a non-king-tide high-tide alert.
        days_until: simulated days until the event (default 7).
    """
    subscribers = db.query(Subscriber).filter(Subscriber.confirmed.is_(True)).all()
    if not subscribers:
        raise HTTPException(status_code=404, detail="No confirmed subscribers found")

    event_dt = datetime.now(timezone.utc) + timedelta(days=days_until)

    notified = 0
    for subscriber in subscribers:
        await send_king_tide_alert(
            subscriber=subscriber,
            period_start=event_dt,
            period_end=event_dt,
            peak_datetime=event_dt,
            peak_height=height,
            days_until=days_until,
        )
        notified += 1

    return TestAlertResponse(message=f"Test alert sent to {notified} subscriber(s)")
