import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NotificationType(str, enum.Enum):
    SEVEN_DAY_ALERT = "seven_day_alert"
    FORTY_EIGHT_HOUR_REMINDER = "forty_eight_hour_reminder"
    CONFIRMATION = "confirmation"


class NotificationSent(Base):
    __tablename__ = "notifications_sent"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    subscriber_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subscribers.id"), nullable=False
    )
    king_tide_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("king_tide_events.id"), nullable=True
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    sent_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    subscriber = relationship("Subscriber", back_populates="notifications")
    king_tide_event = relationship("KingTideEvent", back_populates="notifications")
