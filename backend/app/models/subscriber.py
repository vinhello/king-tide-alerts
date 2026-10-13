import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, String, Uuid
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
    # Lifecycle. Unsubscribing keeps the row and sets unsubscribed_at, so
    # churn is measurable and a later signup reactivates the same record.
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Where the signup came from, captured by the frontend on first page load.
    signup_referrer: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    signup_utm_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    signup_utm_medium: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    signup_utm_campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    signup_landing_path: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
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


def is_active(subscriber: "Subscriber") -> bool:
    """Confirmed and not unsubscribed: the only people who receive alerts."""
    return bool(subscriber.confirmed) and subscriber.unsubscribed_at is None
