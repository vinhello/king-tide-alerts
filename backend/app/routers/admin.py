import hmac
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.email_event import EmailEvent, EmailEventType
from app.models.king_tide_event import KingTideEvent
from app.models.notification_sent import NotificationSent, NotificationType
from app.models.subscriber import NotificationPreference, Subscriber
from app.schemas.admin import (
    AdminEvent,
    AlertRunPreview,
    DailyCount,
    GrowthPoint,
    NotificationHistoryItem,
    NotificationStats,
    NudgeRecipient,
    NudgeResult,
    PlannedAlert,
    SubscriberStats,
    SystemHealth,
    TestAlertResponse,
)
from app.rate_limit import limiter
from app.services import email_events, nudge
from app.services.king_tide_detector import send_alerts
from app.services.notification import build_king_tide_alert_email, send_king_tide_alert
from app.utils.email_templates import confirmation_reminder_email

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
    unsubscribed = (
        db.query(Subscriber).filter(Subscriber.unsubscribed_at.isnot(None)).count()
    )
    active_rows = db.query(Subscriber).filter(Subscriber.unsubscribed_at.is_(None))
    total = active_rows.count()
    confirmed = active_rows.filter(Subscriber.confirmed.is_(True)).count()
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
        unsubscribed=unsubscribed,
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

    # Delivery outcomes reported by Resend, counted per email rather than per
    # event (a delayed message can report several times).
    outcome_rows = (
        db.query(
            EmailEvent.event_type,
            func.count(func.distinct(EmailEvent.provider_message_id)),
        )
        .group_by(EmailEvent.event_type)
        .all()
    )
    outcomes = {event_type: count for event_type, count in outcome_rows}

    # Last 20 notifications, each with its delivery status
    recent_rows = (
        db.query(NotificationSent)
        .join(Subscriber)
        .order_by(NotificationSent.sent_at.desc())
        .limit(20)
        .all()
    )
    events_by_notification: dict = {}
    if recent_rows:
        recent_events = (
            db.query(EmailEvent)
            .filter(EmailEvent.notification_id.in_([n.id for n in recent_rows]))
            .all()
        )
        for event in recent_events:
            events_by_notification.setdefault(event.notification_id, []).append(event)
    recent = [
        NotificationHistoryItem(
            id=str(n.id),
            subscriber_name=n.subscriber.name,
            notification_type=n.notification_type.value,
            sent_at=n.sent_at,
            delivery_status=email_events.delivery_status(
                n, events_by_notification.get(n.id, [])
            ),
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
        delivered=outcomes.get(EmailEventType.DELIVERED, 0),
        bounced=outcomes.get(EmailEventType.BOUNCED, 0),
        complained=outcomes.get(EmailEventType.COMPLAINED, 0),
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
    to: EmailStr = Query(..., description="The one address that receives the test"),
    height: float = Query(default=6.8, ge=5.0, le=20.0),
    days_until: int = Query(default=7, ge=1, le=30),
    _key: str = Depends(verify_admin_auth),
):
    """Send a test alert to exactly one explicit address.

    This never touches the subscriber list: the recipient is a transient
    record built from the `to` parameter, so a test can't reach real users.

    Query params:
        to: the address that receives the test (required).
        height: predicted tide height in ft (default 6.8, king tide).
                Use e.g. 6.2 for a non-king-tide high-tide alert.
        days_until: simulated days until the event (default 7).
    """
    recipient = Subscriber(
        name="Test recipient",
        email=str(to),
        notification_preference=NotificationPreference.EMAIL,
        unsubscribe_token="test-alert",
        confirmed=True,
    )
    event_dt = datetime.now(timezone.utc) + timedelta(days=days_until)

    await send_king_tide_alert(
        subscriber=recipient,
        period_start=event_dt,
        period_end=event_dt,
        peak_datetime=event_dt,
        peak_height=height,
        days_until=days_until,
    )

    return TestAlertResponse(message=f"Test alert sent to {to}")


@router.get("/alerts/preview", response_model=AlertRunPreview)
@limiter.limit("10/minute")
async def preview_alert_run(
    request: Request,
    _key: str = Depends(verify_admin_auth),
    db: Session = Depends(get_db),
):
    """Show what the daily alert run would send right now. Sends nothing."""
    plan = await send_alerts(db, dry_run=True)

    sample_subject = None
    sample_html = None
    if plan.alerts:
        first = plan.alerts[0]
        sample_subject, sample_html = build_king_tide_alert_email(
            name="Subscriber",
            period_start=datetime.combine(
                first.period_start, datetime.min.time(), tzinfo=timezone.utc
            ),
            period_end=datetime.combine(
                first.period_end, datetime.min.time(), tzinfo=timezone.utc
            ),
            peak_datetime=first.peak_datetime,
            peak_height=first.peak_height,
            days_until=first.days_until,
            unsubscribe_url=f"{settings.APP_URL}/unsubscribe",
        )

    return AlertRunPreview(
        dry_run=True,
        subscriber_count=plan.subscriber_count,
        alerts=[
            PlannedAlert(
                notification_type=a.notification_type.value,
                period_start=a.period_start,
                period_end=a.period_end,
                peak_height=a.peak_height,
                peak_datetime=a.peak_datetime,
                days_until=a.days_until,
                recipient_count=a.recipient_count,
            )
            for a in plan.alerts
        ],
        sample_subject=sample_subject,
        sample_email_html=sample_html,
    )


@router.post("/nudge-unconfirmed", response_model=NudgeResult)
@limiter.limit("2/minute")
async def nudge_unconfirmed_signups(
    request: Request,
    dry_run: bool = Query(default=True, description="False actually sends"),
    days: int = Query(default=30, ge=1, le=365),
    _key: str = Depends(verify_admin_auth),
    db: Session = Depends(get_db),
):
    """Remind unconfirmed signups to confirm. Dry run by default.

    A dry run lists who would receive the reminder and shows a sample.
    Only dry_run=false sends, and each recipient is recorded so nobody is
    reminded twice.
    """
    outcome = await nudge.nudge_unconfirmed(db, window_days=days, dry_run=dry_run)

    sample_subject = None
    sample_html = None
    if outcome.recipients:
        sample_subject = "Reminder: confirm your King Tide Alert subscription"
        sample_html = confirmation_reminder_email(
            name="Subscriber",
            confirm_url=f"{settings.APP_URL}/confirm/example",
            signed_up=outcome.recipients[0].signed_up.strftime("%B %-d, %Y"),
        )

    return NudgeResult(
        dry_run=outcome.dry_run,
        window_days=outcome.window_days,
        recipient_count=len(outcome.recipients),
        recipients=[
            NudgeRecipient(name=r.name, email=r.email, signed_up=r.signed_up)
            for r in outcome.recipients
        ],
        sent=outcome.sent,
        sample_subject=sample_subject,
        sample_email_html=sample_html,
    )
