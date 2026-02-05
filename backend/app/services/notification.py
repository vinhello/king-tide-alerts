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
    period_start: datetime,
    period_end: datetime,
    peak_datetime: datetime,
    peak_height: float,
    days_until: int,
) -> None:
    """Send a high tide / king tide alert based on subscriber preference.

    Args:
        subscriber: The subscriber to notify.
        period_start: Start datetime of the tide period.
        period_end: End datetime of the tide period (same as start for single-day).
        peak_datetime: Datetime of the peak tide in the period.
        peak_height: Height of the peak tide in feet.
        days_until: Days until the period starts.
    """
    unsubscribe_url = f"{settings.APP_URL}/unsubscribe/{subscriber.unsubscribe_token}"
    is_king_tide = peak_height >= settings.KING_TIDE_HEIGHT

    # Determine if multi-day period
    is_multi_day = period_start.date() != period_end.date()

    # Format date range
    start_date_str = period_start.strftime("%A, %B %-d")
    if is_multi_day:
        end_date_str = period_end.strftime("%A, %B %-d")
        date_range = f"{start_date_str} – {end_date_str}"
    else:
        date_range = start_date_str

    # Peak tide info
    peak_date = peak_datetime.strftime("%A, %B %-d")
    peak_time = peak_datetime.strftime("%-I:%M %p")

    # Flooding window: ~2 hours before/after peak
    flood_start = peak_datetime - timedelta(hours=2)
    flood_end = peak_datetime + timedelta(hours=2)
    flood_window_start = flood_start.strftime("%-I:%M %p")
    flood_window_end = flood_end.strftime("%-I:%M %p")

    alert_label = "King Tide" if is_king_tide else "High Tide"
    pref = subscriber.notification_preference

    if pref in (NotificationPreference.EMAIL, NotificationPreference.BOTH):
        if subscriber.email:
            html = king_tide_alert_email(
                name=subscriber.name,
                date_range=date_range,
                peak_date=peak_date,
                peak_time=peak_time,
                flood_window_start=flood_window_start,
                flood_window_end=flood_window_end,
                height=peak_height,
                is_king_tide=is_king_tide,
                is_multi_day=is_multi_day,
                days_until=days_until,
                unsubscribe_url=unsubscribe_url,
            )
            subject = f"🌊 {alert_label} Alert — {days_until} days away"
            await send_email(subscriber.email, subject, html)

    if pref in (NotificationPreference.SMS, NotificationPreference.BOTH):
        if subscriber.phone:
            msg = king_tide_alert_sms(
                date_range=date_range,
                peak_date=peak_date,
                peak_time=peak_time,
                flood_window_start=flood_window_start,
                flood_window_end=flood_window_end,
                height=peak_height,
                is_king_tide=is_king_tide,
                is_multi_day=is_multi_day,
                days_until=days_until,
            )
            await send_sms(subscriber.phone, msg)
