"""Ending a subscription, shared by manual unsubscribe and delivery suppression."""

from datetime import datetime, timezone

from app.models.subscriber import Subscriber


def deactivate_and_erase(subscriber: Subscriber) -> bool:
    """Stop all sending and delete the subscriber's personal data.

    Privacy policy: personal data is deleted when a subscription ends. The row
    stays only as an anonymous record (dates and signup source) so churn can
    be counted. The token is kept so a repeated click on the same unsubscribe
    link is still a quiet success rather than an error; it identifies nothing.

    Returns False when the subscription had already ended, so callers can
    tell a change from a repeat.
    """
    if subscriber.unsubscribed_at is not None:
        return False
    subscriber.unsubscribed_at = datetime.now(timezone.utc)
    subscriber.confirmed = False
    subscriber.name = ""
    subscriber.email = None
    subscriber.phone = None
    return True
