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
    event_date: str,
    peak_time: str,
    flood_window_start: str,
    flood_window_end: str,
    height: float,
    is_king_tide: bool,
    days_until: int,
    unsubscribe_url: str,
) -> str:
    urgency = "Heads up" if days_until > 3 else "Reminder"
    alert_type = "King Tide Alert" if is_king_tide else "High Tide Alert"
    king_tide_note = ""
    if is_king_tide:
        king_tide_note = """
        <div style="background-color: #fed7d7; border-left: 4px solid #e53e3e; padding: 12px 16px; margin: 16px 0; border-radius: 4px;">
            <p style="margin: 0; color: #c53030; font-weight: 600;">This is a predicted king tide — expect higher than normal water levels.</p>
        </div>
        """

    return f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #1a365d;">🌊 {alert_type}</h1>
        <p>Hi {name},</p>
        <p><strong>{urgency}:</strong> A high tide of <strong>{height:.1f} ft</strong> is expected in <strong>{days_until} days</strong>. Flooding is possible on low-lying areas and bike paths in Sausalito.</p>
        {king_tide_note}
        <div style="background-color: #ebf8ff; border-left: 4px solid #2b6cb0; padding: 16px; margin: 16px 0; border-radius: 4px;">
            <p style="margin: 0;"><strong>Date:</strong> {event_date}</p>
            <p style="margin: 8px 0 0;"><strong>Peak tide:</strong> {peak_time}</p>
            <p style="margin: 8px 0 0;"><strong>Flooding possible:</strong> {flood_window_start} – {flood_window_end} (estimate)</p>
            <p style="margin: 8px 0 0;"><strong>Predicted height:</strong> {height:.1f} ft</p>
            <p style="margin: 8px 0 0;"><strong>Station:</strong> Sausalito</p>
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
        f"King Tide Alerts: Hi {name}! Confirm your subscription: {confirm_url}"
    )


def king_tide_alert_sms(
    event_date: str,
    peak_time: str,
    flood_window_start: str,
    flood_window_end: str,
    height: float,
    is_king_tide: bool,
    days_until: int,
) -> str:
    label = "King tide" if is_king_tide else "High tide"
    return (
        f"🌊 {label} alert: {height:.1f}ft expected on {event_date}, "
        f"peak at {peak_time}. "
        f"Flooding possible {flood_window_start}–{flood_window_end} in Sausalito. "
        f"Plan alternate routes. "
        f"Times are estimates — follow official guidance. "
        f"kingtidealert.com"
    )
