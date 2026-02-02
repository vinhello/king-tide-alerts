import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.king_tide_event import KingTideEvent
from app.models.notification_sent import NotificationSent, NotificationType
from app.models.subscriber import Subscriber
from app.services import noaa, notification

logger = logging.getLogger(__name__)


def _ensure_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (SQLite strips tzinfo)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def detect_and_store_king_tides(db: Session) -> list[KingTideEvent]:
    """Fetch NOAA predictions and store new king tide events in the database."""
    king_tides = await noaa.get_king_tides(days_ahead=30)
    new_events = []

    for tide in king_tides:
        event_dt = datetime.strptime(tide["datetime"], "%Y-%m-%d %H:%M")
        event_dt = event_dt.replace(tzinfo=timezone.utc)

        # Check if event already exists (within 1 hour window)
        existing = (
            db.query(KingTideEvent)
            .filter(
                KingTideEvent.event_datetime.between(
                    event_dt - timedelta(hours=1),
                    event_dt + timedelta(hours=1),
                ),
                KingTideEvent.station_id == settings.NOAA_STATION_ID,
            )
            .first()
        )

        if existing:
            continue

        event = KingTideEvent(
            event_datetime=event_dt,
            predicted_height=tide["height"],
            station_id=settings.NOAA_STATION_ID,
        )
        db.add(event)
        new_events.append(event)

    db.commit()
    logger.info(f"Stored {len(new_events)} new king tide events")
    return new_events


async def send_alerts(db: Session) -> None:
    """Send 7-day and 48-hour alerts for upcoming king tide events."""
    now = datetime.now(timezone.utc)
    subscribers = (
        db.query(Subscriber).filter(Subscriber.confirmed.is_(True)).all()
    )

    if not subscribers:
        logger.info("No confirmed subscribers, skipping alerts")
        return

    # 7-day alerts: events 5-8 days away (to catch the 7-day window)
    seven_day_events = (
        db.query(KingTideEvent)
        .filter(
            KingTideEvent.event_datetime.between(
                now + timedelta(days=5),
                now + timedelta(days=8),
            ),
            KingTideEvent.seven_day_alert_sent.is_(False),
        )
        .all()
    )

    for event in seven_day_events:
        days_until = (_ensure_aware(event.event_datetime) - now).days
        for subscriber in subscribers:
            # Check if already notified
            existing = (
                db.query(NotificationSent)
                .filter(
                    NotificationSent.subscriber_id == subscriber.id,
                    NotificationSent.king_tide_event_id == event.id,
                    NotificationSent.notification_type
                    == NotificationType.SEVEN_DAY_ALERT,
                )
                .first()
            )
            if existing:
                continue

            await notification.send_king_tide_alert(
                subscriber=subscriber,
                event_datetime=event.event_datetime,
                height=event.predicted_height,
                days_until=days_until,
            )

            db.add(
                NotificationSent(
                    subscriber_id=subscriber.id,
                    king_tide_event_id=event.id,
                    notification_type=NotificationType.SEVEN_DAY_ALERT,
                )
            )

        event.seven_day_alert_sent = True

    # 48-hour alerts: events 1-3 days away
    forty_eight_hour_events = (
        db.query(KingTideEvent)
        .filter(
            KingTideEvent.event_datetime.between(
                now + timedelta(days=1),
                now + timedelta(days=3),
            ),
            KingTideEvent.forty_eight_hour_alert_sent.is_(False),
        )
        .all()
    )

    for event in forty_eight_hour_events:
        days_until = (_ensure_aware(event.event_datetime) - now).days
        for subscriber in subscribers:
            existing = (
                db.query(NotificationSent)
                .filter(
                    NotificationSent.subscriber_id == subscriber.id,
                    NotificationSent.king_tide_event_id == event.id,
                    NotificationSent.notification_type
                    == NotificationType.FORTY_EIGHT_HOUR_REMINDER,
                )
                .first()
            )
            if existing:
                continue

            await notification.send_king_tide_alert(
                subscriber=subscriber,
                event_datetime=event.event_datetime,
                height=event.predicted_height,
                days_until=days_until,
            )

            db.add(
                NotificationSent(
                    subscriber_id=subscriber.id,
                    king_tide_event_id=event.id,
                    notification_type=NotificationType.FORTY_EIGHT_HOUR_REMINDER,
                )
            )

        event.forty_eight_hour_alert_sent = True

    db.commit()
    logger.info(
        f"Sent alerts for {len(seven_day_events)} 7-day events "
        f"and {len(forty_eight_hour_events)} 48-hour events"
    )
