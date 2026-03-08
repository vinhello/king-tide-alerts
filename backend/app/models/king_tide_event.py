import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class KingTideEvent(Base):
    __tablename__ = "king_tide_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    predicted_height: Mapped[float] = mapped_column(nullable=False)
    station_id: Mapped[str] = mapped_column(nullable=False)
    seven_day_alert_sent: Mapped[bool] = mapped_column(default=False, nullable=False)
    forty_eight_hour_alert_sent: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    notifications = relationship("NotificationSent", back_populates="king_tide_event")
