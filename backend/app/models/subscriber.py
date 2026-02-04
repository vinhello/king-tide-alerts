import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy import Uuid
from sqlalchemy.orm import relationship

from app.database import Base


class NotificationPreference(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, unique=True, nullable=True)
    notification_preference = Column(
        Enum(NotificationPreference, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    unsubscribe_token = Column(String, unique=True, nullable=False)
    confirmed = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    notifications = relationship("NotificationSent", back_populates="subscriber")
