import html
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.tide_residual import ResidualSummary


def confirmation_email(name: str, confirm_url: str) -> str:
    return f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #1a365d;">King Tide Alerts</h1>
        <p>Hi {name},</p>
        <p>Thanks for subscribing to King Tide Alerts for the SF Bay Area! Please confirm your subscription by clicking the button below:</p>
        <a href="{confirm_url}" style="display: inline-block; background-color: #2b6cb0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 16px 0;">Confirm Subscription</a>
        <p>Once confirmed, you'll receive alerts when high tides are forecasted that could cause flooding on low-lying areas and bike paths in Sausalito.</p>
        <p>Visit <a href="https://kingtidealert.com" style="color: #2b6cb0;">kingtidealert.com</a> to view upcoming tides.</p>
        <p style="color: #718096; font-size: 14px;">If you didn't sign up for this, you can safely ignore this email.</p>
    </body>
    </html>
    """


def king_tide_alert_email(
    name: str,
    date_range: str,
    peak_date: str,
    peak_time: str,
    flood_window_start: str,
    flood_window_end: str,
    height: float,
    is_king_tide: bool,
    is_multi_day: bool,
    days_until: int,
    unsubscribe_url: str,
    residual: "ResidualSummary | None" = None,
) -> str:
    residual_note = residual_sentence(residual)
    urgency = "Heads up" if days_until > 3 else "Reminder"
    emoji = "👑🌊" if is_king_tide else "🌊"
    alert_type = "King Tide Alert" if is_king_tide else "High Tide Alert"
    king_tide_note = ""
    if is_king_tide:
        king_tide_note = """
        <div style="background-color: #fed7d7; border-left: 4px solid #e53e3e; padding: 12px 16px; margin: 16px 0; border-radius: 4px;">
            <p style="margin: 0; color: #c53030; font-weight: 600;">This is a predicted king tide — expect higher than normal water levels.</p>
        </div>
        """

    if is_multi_day:
        tide_summary = (
            f"High tides are expected <strong>{date_range}</strong>, "
            f"peaking at <strong>{height:.1f} ft</strong> on <strong>{peak_date}</strong>."
        )
    else:
        tide_summary = (
            f"A high tide of <strong>{height:.1f} ft</strong> is expected on "
            f"<strong>{date_range}</strong>."
        )

    return f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #1a365d;">{emoji} {alert_type}</h1>
        <p>Hi {name},</p>
        <p><strong>{urgency}:</strong> {tide_summary} Flooding is possible on low-lying areas and bike paths in Sausalito.</p>
        {king_tide_note}
        <div style="background-color: #ebf8ff; border-left: 4px solid #2b6cb0; padding: 16px; margin: 16px 0; border-radius: 4px;">
            <p style="margin: 0;"><strong>Dates:</strong> {date_range}</p>
            <p style="margin: 8px 0 0;"><strong>Peak tide:</strong> {peak_time} on {peak_date}</p>
            <p style="margin: 8px 0 0;"><strong>Flooding possible:</strong> {flood_window_start} – {flood_window_end} (estimate, around peak)</p>
            <p style="margin: 8px 0 0;"><strong>Peak height:</strong> {height:.1f} ft</p>
            <p style="margin: 8px 0 0;"><strong>Gauge:</strong> San Francisco (Golden Gate), NOAA 9414290</p>
            {residual_note}
        </div>
        <p>Consider alternate routes or plan your ride around the flooding window.</p>
        <p style="margin-top: 16px;">
            <a href="https://kingtidealert.com" style="color: #2b6cb0;">kingtidealert.com</a> — View upcoming tides and manage your subscription.
        </p>
        <p style="color: #718096; font-size: 13px; margin-top: 24px; line-height: 1.5;">
            <strong>Disclaimer:</strong> Flooding times are estimates based on predicted tide data from NOAA.
            Actual conditions may vary due to weather, wind, and other factors.
            This alert is informational only — please follow official guidance from the
            National Weather Service and local authorities.
        </p>
        <p style="color: #718096; font-size: 14px; margin-top: 16px;">
            <a href="{unsubscribe_url}" style="color: #718096;">Unsubscribe</a> from King Tide Alerts
        </p>
    </body>
    </html>
    """


def confirmation_sms(name: str, confirm_url: str) -> str:
    return (
        f"King Tide Alerts: Hi {name}! Confirm your subscription: {confirm_url} "
        f"Reply STOP to opt out."
    )


def king_tide_alert_sms(
    date_range: str,
    peak_date: str,
    peak_time: str,
    flood_window_start: str,
    flood_window_end: str,
    height: float,
    is_king_tide: bool,
    is_multi_day: bool,
    days_until: int,
) -> str:
    label = "King tide" if is_king_tide else "High tide"
    if is_multi_day:
        return (
            f"King Tide Alerts: {label} {date_range}, "
            f"peaking at {height:.1f}ft on {peak_date} at {peak_time}. "
            f"Flooding possible {flood_window_start}-{flood_window_end} in Sausalito. "
            f"Plan alternate routes. "
            f"Reply STOP to opt out. kingtidealert.com"
        )
    return (
        f"King Tide Alerts: {label} of {height:.1f}ft expected {date_range}, "
        f"peak at {peak_time}. "
        f"Flooding possible {flood_window_start}-{flood_window_end} in Sausalito. "
        f"Plan alternate routes. "
        f"Reply STOP to opt out. kingtidealert.com"
    )


def feedback_email(subject: str, message: str, reply_email: str | None) -> str:
    """Render a visitor's feedback for the project inbox.

    Visitor-supplied text is HTML-escaped so a message can't inject markup.
    """
    safe_subject = html.escape(subject)
    safe_message = html.escape(message).replace("\n", "<br>")
    if reply_email:
        safe_reply = html.escape(reply_email)
        reply_line = f'<a href="mailto:{safe_reply}" style="color: #2b6cb0;">{safe_reply}</a>'
    else:
        reply_line = "not provided"

    return f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #1a365d; font-size: 20px;">Website feedback</h1>
        <p><strong>Subject:</strong> {safe_subject}</p>
        <p><strong>Reply to:</strong> {reply_line}</p>
        <div style="background-color: #f7fafc; border-left: 4px solid #2b6cb0; padding: 16px; margin: 16px 0; border-radius: 4px; white-space: normal;">
            {safe_message}
        </div>
        <p style="color: #718096; font-size: 13px;">Sent from the feedback form at kingtidealert.com.</p>
    </body>
    </html>
    """


def residual_sentence(residual: "ResidualSummary | None") -> str:
    """One measured, dated sentence for the alert details box, or empty."""
    if residual is None:
        return ""
    magnitude = abs(residual.mean_residual_ft)
    if magnitude < 0.05:
        comparison = "matched NOAA's predictions"
    else:
        direction = "above" if residual.mean_residual_ft > 0 else "below"
        comparison = f"averaged {magnitude:.1f} ft {direction} NOAA's predictions"
    return (
        '<p style="margin: 8px 0 0;"><strong>Measured recently:</strong> over the '
        f"{residual.window_days} days ending {residual.as_of}, water at this gauge "
        f"{comparison}. Actual levels may differ from the predicted height above.</p>"
    )
