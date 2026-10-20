"""Delivery outcomes reported by Resend, and the suppression rule they drive.

Resend posts one webhook per event. Only delivery outcomes are handled here
(delivered, delayed, bounced, complained); open and click tracking stays off.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.email_event import EmailEvent, EmailEventType
from app.models.notification_sent import NotificationSent
from app.models.subscriber import Subscriber
from app.services.subscriber_lifecycle import deactivate_and_erase

logger = logging.getLogger(__name__)

# Resend event type -> what we store. Anything else is acknowledged and dropped.
HANDLED_EVENTS: dict[str, EmailEventType] = {
    "email.delivered": EmailEventType.DELIVERED,
    "email.delivery_delayed": EmailEventType.DELIVERY_DELAYED,
    "email.bounced": EmailEventType.BOUNCED,
    "email.complained": EmailEventType.COMPLAINED,
}

# Outcomes of handling one webhook, returned to Resend and logged.
RECORDED = "recorded"
SUPPRESSED = "suppressed"
DUPLICATE = "duplicate"
IGNORED = "ignored"

MAX_DETAIL_LENGTH = 500


def record_event(db: Session, svix_id: str, event: Mapping[str, Any]) -> str:
    """Store one verified Resend event and suppress the subscriber when warranted.

    Idempotent on svix_id: Resend retries a webhook with the same id, so a
    repeat is acknowledged without a second row. Returns RECORDED, SUPPRESSED,
    DUPLICATE or IGNORED.
    """
    event_type = HANDLED_EVENTS.get(str(event.get("type", "")))
    data = event.get("data") or {}
    message_id = data.get("email_id")
    if event_type is None or not isinstance(message_id, str) or not message_id:
        return IGNORED

    if db.query(EmailEvent).filter(EmailEvent.svix_id == svix_id).first():
        return DUPLICATE

    notification = (
        db.query(NotificationSent)
        .filter(NotificationSent.provider_message_id == message_id)
        .first()
    )
    if notification is not None:
        subscriber = notification.subscriber
    else:
        subscriber = _subscriber_for(db, data.get("to"))

    bounce = data.get("bounce") or {}
    bounce_type = _text(bounce.get("type"), 50)
    db.add(
        EmailEvent(
            svix_id=svix_id,
            provider_message_id=message_id,
            notification_id=notification.id if notification else None,
            subscriber_id=subscriber.id if subscriber else None,
            event_type=event_type,
            bounce_type=bounce_type,
            detail=_detail(event_type, bounce),
            occurred_at=_parse_timestamp(event.get("created_at")),
        )
    )

    outcome = RECORDED
    if subscriber is not None and should_suppress(event_type, bounce_type):
        if deactivate_and_erase(subscriber):
            outcome = SUPPRESSED

    try:
        db.commit()
    except IntegrityError:
        # Lost a race with a retry of the same event; the first one won.
        db.rollback()
        return DUPLICATE

    if outcome == SUPPRESSED:
        logger.warning(
            f"Stopped sending to subscriber {subscriber.id} after "
            f"{event_type.value} ({bounce_type or 'no bounce type'})"
        )
    else:
        logger.info(f"Resend {event_type.value} for message {message_id}: {outcome}")
    return outcome


def relink_orphans(db: Session) -> int:
    """Attach events that arrived before their send row was committed.

    Resend can report a delivery within seconds of a send, so a webhook may
    land before the alert run has committed the row for that message. Such
    an event is stored without a notification link; this pairs it up by
    message id afterwards. Events for emails that never get a row (signup
    confirmations) stay as they are. Returns how many were linked.
    """
    pairs = (
        db.query(EmailEvent, NotificationSent.id)
        .join(
            NotificationSent,
            NotificationSent.provider_message_id == EmailEvent.provider_message_id,
        )
        .filter(EmailEvent.notification_id.is_(None))
        .all()
    )
    for event, notification_id in pairs:
        event.notification_id = notification_id
    if pairs:
        db.commit()
    return len(pairs)


def should_suppress(event_type: EmailEventType, bounce_type: str | None) -> bool:
    """A spam complaint or a permanent (hard) bounce ends the subscription.

    Temporary bounces (full mailbox, greylisting) are recorded and nothing
    more, because the address usually works again.
    """
    if event_type is EmailEventType.COMPLAINED:
        return True
    if event_type is EmailEventType.BOUNCED:
        return (bounce_type or "").lower() == "permanent"
    return False


# Shown per send on the admin page. Earlier entries win when several apply.
_STATUS_PRIORITY = (
    EmailEventType.BOUNCED,
    EmailEventType.COMPLAINED,
    EmailEventType.DELIVERED,
    EmailEventType.DELIVERY_DELAYED,
)


def delivery_status(notification: NotificationSent, events: list[EmailEvent]) -> str:
    """One word for a send: its recorded outcome, else "sent" (accepted by
    Resend, no outcome yet) or "unknown" (sent before outcomes were kept)."""
    seen = {e.event_type for e in events}
    for event_type in _STATUS_PRIORITY:
        if event_type in seen:
            return event_type.value
    return "sent" if notification.provider_message_id else "unknown"


def _subscriber_for(db: Session, to: Any) -> Subscriber | None:
    """Match by recipient for emails that have no notification row, such as
    signup confirmations. The address is used for the lookup and not kept."""
    if isinstance(to, list):
        to = to[0] if to else None
    if not isinstance(to, str) or not to.strip():
        return None
    return (
        db.query(Subscriber)
        .filter(func.lower(Subscriber.email) == to.strip().lower())
        .first()
    )


def _detail(event_type: EmailEventType, bounce: Mapping[str, Any]) -> str | None:
    if event_type is not EmailEventType.BOUNCED:
        return None
    parts = [
        _text(bounce.get("subType"), 100),
        _text(bounce.get("message"), MAX_DETAIL_LENGTH),
    ]
    text = ": ".join(p for p in parts if p)
    return text[:MAX_DETAIL_LENGTH] or None


def _text(value: Any, limit: int) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value[:limit]


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            pass
    return datetime.now(timezone.utc)
