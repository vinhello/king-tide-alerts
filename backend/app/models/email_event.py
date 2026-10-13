import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EmailEventType(str, enum.Enum):
    DELIVERED = "delivered"
    DELIVERY_DELAYED = "delivery_delayed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


class EmailEvent(Base):
    """A delivery outcome Resend reported for one email we sent.

    Only delivery outcomes are kept (delivered, delayed, bounced, complained);
    opens and clicks are not tracked. The recipient address is never stored
    here: a row links to the notification and subscriber it belongs to when
    they can be found, and stands alone otherwise.
    """

    __tablename__ = "email_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Resend retries a webhook with the same svix-id, so it is the idempotency key.
    svix_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # Resend's id for the email, as returned when it was sent.
    provider_message_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    notification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("notifications_sent.id"), nullable=True, index=True
    )
    subscriber_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("subscribers.id"), nullable=True
    )
    event_type: Mapped[EmailEventType] = mapped_column(
        Enum(EmailEventType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    # Bounces only: "Permanent" or "Temporary", and the receiving server's reason.
    bounce_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # When Resend says it happened, and when we received it.
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    notification = relationship("NotificationSent", back_populates="email_events")
