from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class SubscriberStats(BaseModel):
    total: int
    confirmed: int
    unconfirmed: int
    unsubscribed: int = 0
    email_only: int
    sms_only: int
    both: int
    growth: list["GrowthPoint"]


class GrowthPoint(BaseModel):
    date: str
    count: int


class NotificationStats(BaseModel):
    total_sent: int
    seven_day_alerts: int
    forty_eight_hour_reminders: int
    confirmations: int
    # Delivery outcomes Resend reported, counted per email.
    delivered: int = 0
    bounced: int = 0
    complained: int = 0
    recent: list["NotificationHistoryItem"]
    daily_counts: list["DailyCount"]


class NotificationHistoryItem(BaseModel):
    id: str
    subscriber_name: str
    notification_type: str
    sent_at: datetime
    # delivered, delivery_delayed, bounced, complained, sent (no outcome yet)
    # or unknown (sent before outcomes were recorded).
    delivery_status: str = "unknown"


class DailyCount(BaseModel):
    date: str
    count: int


class AdminEvent(BaseModel):
    id: str
    event_datetime: datetime
    predicted_height: float
    seven_day_alert_sent: bool
    forty_eight_hour_alert_sent: bool
    notifications_sent: int


class SystemHealth(BaseModel):
    scheduler_running: bool
    next_run_time: Optional[str]
    environment: str
    latest_event_at: Optional[datetime]


class TestAlertResponse(BaseModel):
    message: str


class PlannedAlert(BaseModel):
    notification_type: str
    period_start: date
    period_end: date
    peak_height: float
    peak_datetime: datetime
    days_until: int
    recipient_count: int


class AlertRunPreview(BaseModel):
    """What the daily run would send right now. Produced without sending."""

    dry_run: bool
    subscriber_count: int
    alerts: list[PlannedAlert]
    sample_subject: Optional[str]
    sample_email_html: Optional[str]


class NudgeRecipient(BaseModel):
    name: str
    email: str
    signed_up: datetime


class NudgeResult(BaseModel):
    """Outcome of a nudge run. dry_run=True means nothing was sent."""

    dry_run: bool
    window_days: int
    recipient_count: int
    recipients: list[NudgeRecipient]
    sent: int
    sample_subject: Optional[str]
    sample_email_html: Optional[str]


class FunnelStage(BaseModel):
    signups: int
    confirmed: int
    confirmation_rate: float
    median_hours_to_confirm: Optional[float]
    unsubscribed: int
    nudged: int
    confirmed_after_nudge: int


class FunnelSource(BaseModel):
    source: str
    signups: int
    confirmed: int


class FunnelWeek(BaseModel):
    week_start: str
    signups: int
    confirmed: int
    unsubscribed: int


class FunnelRun(BaseModel):
    date: str
    notification_type: str
    sent: int
    delivered: int
    bounced: int
    complained: int
    no_outcome: int


class FunnelStats(BaseModel):
    """Signup-to-delivery funnel for the admin page. Read-only."""

    all_time: FunnelStage
    last_30_days: FunnelStage
    by_source: list[FunnelSource]
    weekly: list[FunnelWeek]
    runs: list[FunnelRun]
