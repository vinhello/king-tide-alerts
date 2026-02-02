def confirmation_email(name: str, confirm_url: str) -> str:
    return f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #1a365d;">King Tide Alerts</h1>
        <p>Hi {name},</p>
        <p>Thanks for subscribing to King Tide Alerts for the SF Bay Area! Please confirm your subscription by clicking the button below:</p>
        <a href="{confirm_url}" style="display: inline-block; background-color: #2b6cb0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 16px 0;">Confirm Subscription</a>
        <p>Once confirmed, you'll receive alerts when king tides are forecasted that could cause flooding on Bay Trail bike routes through Sausalito.</p>
        <p style="color: #718096; font-size: 14px;">If you didn't sign up for this, you can safely ignore this email.</p>
    </body>
    </html>
    """


def king_tide_alert_email(
    name: str,
    event_datetime: str,
    height: float,
    days_until: int,
    unsubscribe_url: str,
) -> str:
    urgency = "Heads up" if days_until > 3 else "Reminder"
    return f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #1a365d;">🌊 King Tide Alert</h1>
        <p>Hi {name},</p>
        <p><strong>{urgency}:</strong> A king tide is forecasted in <strong>{days_until} days</strong>.</p>
        <div style="background-color: #ebf8ff; border-left: 4px solid #2b6cb0; padding: 16px; margin: 16px 0; border-radius: 4px;">
            <p style="margin: 0;"><strong>When:</strong> {event_datetime}</p>
            <p style="margin: 8px 0 0;"><strong>Predicted height:</strong> {height:.1f} ft above MHHW</p>
            <p style="margin: 8px 0 0;"><strong>Station:</strong> San Francisco / Golden Gate</p>
        </div>
        <p>The Bay Trail through Sausalito may experience flooding. Consider alternate routes or plan your ride accordingly.</p>
        <p style="color: #718096; font-size: 14px; margin-top: 32px;">
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
    event_datetime: str,
    height: float,
    days_until: int,
) -> str:
    return (
        f"🌊 King Tide Alert: {height:.1f}ft above MHHW expected on {event_datetime} "
        f"({days_until} days away). Bay Trail through Sausalito may flood. "
        f"Plan alternate routes."
    )
