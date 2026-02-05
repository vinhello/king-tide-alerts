import logging
from datetime import datetime, timedelta

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
                "from": "King Tide Alerts <alert@alert.kingtidealert.com>",
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
    """Send a high tide / king tide alert based on subscriber preference."""
    unsubscribe_url = f"{settings.APP_URL}/unsubscribe/{subscriber.unsubscribe_token}"
    is_king_tide = height >= settings.KING_TIDE_HEIGHT

    # Compute flooding window: ~2 hours before/after peak
    if isinstance(event_datetime, datetime):
        peak_dt = event_datetime
    else:
        peak_dt = datetime.strptime(str(event_datetime), "%Y-%m-%d %H:%M")

    flood_start = peak_dt - timedelta(hours=2)
    flood_end = peak_dt + timedelta(hours=2)

    event_date = peak_dt.strftime("%A, %B %d, %Y")
    peak_time = peak_dt.strftime("%I:%M %p").lstrip("0")
    flood_window_start = flood_start.strftime("%I:%M %p").lstrip("0")
    flood_window_end = flood_end.strftime("%I:%M %p").lstrip("0")

    alert_label = "King Tide" if is_king_tide else "High Tide"
    pref = subscriber.notification_preference

    if pref in (NotificationPreference.EMAIL, NotificationPreference.BOTH):
        if subscriber.email:
            html = king_tide_alert_email(
                name=subscriber.name,
                event_date=event_date,
                peak_time=peak_time,
                flood_window_start=flood_window_start,
                flood_window_end=flood_window_end,
                height=height,
                is_king_tide=is_king_tide,
                days_until=days_until,
                unsubscribe_url=unsubscribe_url,
            )
            subject = f"🌊 {alert_label} Alert — {days_until} days away"
            await send_email(subscriber.email, subject, html)

    if pref in (NotificationPreference.SMS, NotificationPreference.BOTH):
        if subscriber.phone:
            msg = king_tide_alert_sms(
                event_date=event_date,
                peak_time=peak_time,
                flood_window_start=flood_window_start,
                flood_window_end=flood_window_end,
                height=height,
                is_king_tide=is_king_tide,
                days_until=days_until,
            )
            await send_sms(subscriber.phone, msg)
