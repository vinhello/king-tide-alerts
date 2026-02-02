import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Uuid
from sqlalchemy.orm import relationship

from app.database import Base


class NotificationType(str, enum.Enum):
    SEVEN_DAY_ALERT = "seven_day_alert"
    FORTY_EIGHT_HOUR_REMINDER = "forty_eight_hour_reminder"
    CONFIRMATION = "confirmation"


class NotificationSent(Base):
    __tablename__ = "notifications_sent"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    subscriber_id = Column(
        Uuid, ForeignKey("subscribers.id"), nullable=False
    )
    king_tide_event_id = Column(
        Uuid, ForeignKey("king_tide_events.id"), nullable=True
    )
    notification_type = Column(Enum(NotificationType), nullable=False)
    sent_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    subscriber = relationship("Subscriber", back_populates="notifications")
    king_tide_event = relationship("KingTideEvent", back_populates="notifications")
