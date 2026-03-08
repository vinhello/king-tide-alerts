import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Enum, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NotificationPreference(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"


class Subscriber(Base):
    __tablename__ = "subscribers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[Optional[str]] = mapped_column(unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(unique=True, nullable=True)
    notification_preference: Mapped[NotificationPreference] = mapped_column(
        Enum(NotificationPreference, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    unsubscribe_token: Mapped[str] = mapped_column(unique=True, nullable=False)
    confirmed: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    notifications = relationship("NotificationSent", back_populates="subscriber")
