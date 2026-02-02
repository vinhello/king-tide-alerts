import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, String, Uuid
from sqlalchemy.orm import relationship

from app.database import Base


class KingTideEvent(Base):
    __tablename__ = "king_tide_events"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    event_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    predicted_height = Column(Float, nullable=False)
    station_id = Column(String, nullable=False)
    seven_day_alert_sent = Column(Boolean, default=False, nullable=False)
    forty_eight_hour_alert_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    notifications = relationship("NotificationSent", back_populates="king_tide_event")
