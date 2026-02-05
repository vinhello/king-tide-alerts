import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

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


@dataclass
class TidePeriod:
    """A group of consecutive days that each have at least one high tide event."""

    start_date: date
    end_date: date
    peak_height: float
    peak_datetime: datetime
    event_ids: list = field(default_factory=list)


def _group_into_periods(events: list[KingTideEvent]) -> list[TidePeriod]:
    """Group events into tide periods of consecutive calendar days.

    Events on consecutive days are merged into one period. A gap of 1+ days
    with no events starts a new period.
    """
    if not events:
        return []

    sorted_events = sorted(events, key=lambda e: _ensure_aware(e.event_datetime))

    periods: list[TidePeriod] = []
    current_events = [sorted_events[0]]

    for event in sorted_events[1:]:
        prev_date = _ensure_aware(current_events[-1].event_datetime).date()
        curr_date = _ensure_aware(event.event_datetime).date()
        gap = (curr_date - prev_date).days

        if gap <= 1:
            # Same day or next day — same period
            current_events.append(event)
        else:
            # Gap — finalize current period and start new one
            periods.append(_make_period(current_events))
            current_events = [event]

    # Finalize last period
    periods.append(_make_period(current_events))
    return periods


def _make_period(events: list[KingTideEvent]) -> TidePeriod:
    """Create a TidePeriod from a list of events."""
    peak_event = max(events, key=lambda e: e.predicted_height)
    return TidePeriod(
        start_date=_ensure_aware(events[0].event_datetime).date(),
        end_date=_ensure_aware(events[-1].event_datetime).date(),
        peak_height=peak_event.predicted_height,
        peak_datetime=_ensure_aware(peak_event.event_datetime),
        event_ids=[e.id for e in events],
    )


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
    """Send 7-day and 48-hour alerts for upcoming king tide events.

    Events are grouped into tide periods (consecutive calendar days).
    One alert is sent per period per subscriber, not per event.
    """
    now = datetime.now(timezone.utc)
    today = now.date()

    subscribers = (
        db.query(Subscriber).filter(Subscriber.confirmed.is_(True)).all()
    )

    if not subscribers:
        logger.info("No confirmed subscribers, skipping alerts")
        return

    # Query all upcoming events in the next 30 days
    upcoming_events = (
        db.query(KingTideEvent)
        .filter(
            KingTideEvent.event_datetime >= now,
            KingTideEvent.event_datetime <= now + timedelta(days=30),
        )
        .order_by(KingTideEvent.event_datetime)
        .all()
    )

    if not upcoming_events:
        logger.info("No upcoming events found")
        return

    periods = _group_into_periods(upcoming_events)
    seven_day_count = 0
    forty_eight_hour_count = 0

    for period in periods:
        days_until = (period.start_date - today).days

        # 7-day alert: period starts in 5-8 days
        if 5 <= days_until <= 8:
            # Check if ANY event in this period already had 7-day alert sent
            already_alerted = (
                db.query(KingTideEvent)
                .filter(
                    KingTideEvent.id.in_(period.event_ids),
                    KingTideEvent.seven_day_alert_sent.is_(True),
                )
                .first()
            )
            if not already_alerted:
                await _send_period_alert(
                    db=db,
                    subscribers=subscribers,
                    period=period,
                    days_until=days_until,
                    notification_type=NotificationType.SEVEN_DAY_ALERT,
                )
                # Mark all events in period as alerted
                db.query(KingTideEvent).filter(
                    KingTideEvent.id.in_(period.event_ids)
                ).update(
                    {KingTideEvent.seven_day_alert_sent: True},
                    synchronize_session="fetch",
                )
                seven_day_count += 1

        # 48-hour alert: period starts in 1-3 days
        if 1 <= days_until <= 3:
            already_alerted = (
                db.query(KingTideEvent)
                .filter(
                    KingTideEvent.id.in_(period.event_ids),
                    KingTideEvent.forty_eight_hour_alert_sent.is_(True),
                )
                .first()
            )
            if not already_alerted:
                await _send_period_alert(
                    db=db,
                    subscribers=subscribers,
                    period=period,
                    days_until=days_until,
                    notification_type=NotificationType.FORTY_EIGHT_HOUR_REMINDER,
                )
                db.query(KingTideEvent).filter(
                    KingTideEvent.id.in_(period.event_ids)
                ).update(
                    {KingTideEvent.forty_eight_hour_alert_sent: True},
                    synchronize_session="fetch",
                )
                forty_eight_hour_count += 1

    db.commit()
    logger.info(
        f"Sent alerts for {seven_day_count} 7-day periods "
        f"and {forty_eight_hour_count} 48-hour periods"
    )


async def _send_period_alert(
    db: Session,
    subscribers: list[Subscriber],
    period: TidePeriod,
    days_until: int,
    notification_type: NotificationType,
) -> None:
    """Send one alert per subscriber for a tide period.

    Creates a single NotificationSent record per subscriber, linked to the
    peak event in the period.
    """
    # Find the peak event ID (the one with highest predicted_height)
    peak_event = (
        db.query(KingTideEvent)
        .filter(KingTideEvent.id.in_(period.event_ids))
        .order_by(KingTideEvent.predicted_height.desc())
        .first()
    )
    peak_event_id = peak_event.id if peak_event else period.event_ids[0]

    for subscriber in subscribers:
        # Check if already notified for this period (via any event in it)
        existing = (
            db.query(NotificationSent)
            .filter(
                NotificationSent.subscriber_id == subscriber.id,
                NotificationSent.king_tide_event_id.in_(period.event_ids),
                NotificationSent.notification_type == notification_type,
            )
            .first()
        )
        if existing:
            continue

        # Build period_start / period_end as datetimes for the notification
        period_start_dt = datetime.combine(
            period.start_date, datetime.min.time(), tzinfo=timezone.utc
        )
        period_end_dt = datetime.combine(
            period.end_date, datetime.min.time(), tzinfo=timezone.utc
        )

        await notification.send_king_tide_alert(
            subscriber=subscriber,
            period_start=period_start_dt,
            period_end=period_end_dt,
            peak_datetime=period.peak_datetime,
            peak_height=period.peak_height,
            days_until=days_until,
        )

        db.add(
            NotificationSent(
                subscriber_id=subscriber.id,
                king_tide_event_id=peak_event_id,
                notification_type=notification_type,
            )
        )
