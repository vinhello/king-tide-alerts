from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SubscriberStats(BaseModel):
    total: int
    confirmed: int
    unconfirmed: int
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
    recent: list["NotificationHistoryItem"]
    daily_counts: list["DailyCount"]


class NotificationHistoryItem(BaseModel):
    id: str
    subscriber_name: str
    notification_type: str
    sent_at: datetime


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
