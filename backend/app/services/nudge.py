"""One-time reminder to people who signed up but never confirmed.

Dry run is the default everywhere this is exposed. A real send records a
`confirmation` notification per recipient, which both documents the nudge
and keeps anyone from being nudged twice.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_sent import NotificationSent, NotificationType
from app.models.subscriber import Subscriber
from app.services import notification

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NudgeRecipient:
    name: str
    email: str
    signed_up: datetime


@dataclass
class NudgeOutcome:
    dry_run: bool
    window_days: int
    recipients: list[NudgeRecipient] = field(default_factory=list)
    sent: int = 0


def find_unconfirmed(db: Session, window_days: int) -> list[Subscriber]:
    """Unconfirmed email signups within the window that have not been nudged."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    already_nudged = select(NotificationSent.subscriber_id).where(
        NotificationSent.notification_type == NotificationType.CONFIRMATION
    )
    return (
        db.query(Subscriber)
        .filter(
            Subscriber.confirmed.is_(False),
            Subscriber.unsubscribed_at.is_(None),
            Subscriber.email.isnot(None),
            Subscriber.created_at >= cutoff,
            ~Subscriber.id.in_(already_nudged),
        )
        .order_by(Subscriber.created_at)
        .all()
    )


async def nudge_unconfirmed(
    db: Session, window_days: int = 30, dry_run: bool = True
) -> NudgeOutcome:
    """Send (or, by default, only plan) one reminder per unconfirmed signup."""
    subscribers = find_unconfirmed(db, window_days)
    outcome = NudgeOutcome(
        dry_run=dry_run,
        window_days=window_days,
        recipients=[
            NudgeRecipient(name=s.name, email=s.email or "", signed_up=s.created_at)
            for s in subscribers
        ],
    )
    if dry_run:
        logger.info(f"Nudge dry run: {len(subscribers)} unconfirmed signups in {window_days} days")
        return outcome

    for subscriber in subscribers:
        await notification.send_confirmation_reminder(subscriber)
        db.add(
            NotificationSent(
                subscriber_id=subscriber.id,
                king_tide_event_id=None,
                notification_type=NotificationType.CONFIRMATION,
            )
        )
        outcome.sent += 1
    db.commit()
    logger.info(f"Nudge sent to {outcome.sent} unconfirmed signups")
    return outcome
