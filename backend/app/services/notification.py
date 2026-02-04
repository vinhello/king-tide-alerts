import logging
from datetime import datetime

import resend
from twilio.rest import Client as TwilioClient

from app.config import settings
from app.models.subscriber import NotificationPreference, Subscriber
from app.utils.email_templates import (
    confirmation_email,
    confirmation_sms,
    king_tide_alert_email,
    king_tide_alert_sms,
)

logger = logging.getLogger(__name__)


def _get_twilio_client() -> TwilioClient:
    return TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


async def send_email(to: str, subject: str, html: str) -> None:
    """Send an email via Resend."""
    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send(
            {
                "from": "King Tide Alerts <alert@kingtidealert.com>",
                "to": [to],
                "subject": subject,
                "html": html,
            }
        )
        logger.info(f"Email sent to {to}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")


async def send_sms(to: str, message: str) -> None:
    """Send an SMS via Twilio."""
    try:
        client = _get_twilio_client()
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to,
        )
        logger.info(f"SMS sent to {to}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {to}: {e}")


async def send_confirmation(subscriber: Subscriber) -> None:
    """Send confirmation email/SMS to a new subscriber."""
    confirm_url = f"{settings.APP_URL}/confirm/{subscriber.unsubscribe_token}"
    pref = subscriber.notification_preference

    if pref in (NotificationPreference.EMAIL, NotificationPreference.BOTH):
        if subscriber.email:
            html = confirmation_email(subscriber.name, confirm_url)
            await send_email(
                subscriber.email, "Confirm your King Tide Alerts subscription", html
            )

    if pref in (NotificationPreference.SMS, NotificationPreference.BOTH):
        if subscriber.phone:
            msg = confirmation_sms(subscriber.name, confirm_url)
            await send_sms(subscriber.phone, msg)


async def send_king_tide_alert(
    subscriber: Subscriber,
    event_datetime: datetime,
    height: float,
    days_until: int,
) -> None:
    """Send a king tide alert to a subscriber based on their preference."""

    unsubscribe_url = f"{settings.APP_URL}/unsubscribe/{subscriber.unsubscribe_token}"

    if isinstance(event_datetime, datetime):
        event_dt_str = event_datetime.strftime("%B %d, %Y at %I:%M %p")
    else:
        event_dt_str = str(event_datetime)

    pref = subscriber.notification_preference

    if pref in (NotificationPreference.EMAIL, NotificationPreference.BOTH):
        if subscriber.email:
            html = king_tide_alert_email(
                name=subscriber.name,
                event_datetime=event_dt_str,
                height=height,
                days_until=days_until,
                unsubscribe_url=unsubscribe_url,
            )
            subject = f"🌊 King Tide Alert — {days_until} days away"
            await send_email(subscriber.email, subject, html)

    if pref in (NotificationPreference.SMS, NotificationPreference.BOTH):
        if subscriber.phone:
            msg = king_tide_alert_sms(
                event_datetime=event_dt_str,
                height=height,
                days_until=days_until,
            )
            await send_sms(subscriber.phone, msg)
