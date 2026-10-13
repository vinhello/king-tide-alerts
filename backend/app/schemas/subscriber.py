from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.subscriber import NotificationPreference


class SubscribeRequest(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    notification_preference: NotificationPreference
    # Optional attribution captured by the frontend on first page load.
    signup_referrer: str | None = Field(default=None, max_length=500)
    signup_utm_source: str | None = Field(default=None, max_length=100)
    signup_utm_medium: str | None = Field(default=None, max_length=100)
    signup_utm_campaign: str | None = Field(default=None, max_length=100)
    signup_landing_path: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_contact_info(self) -> "SubscribeRequest":
        pref = self.notification_preference
        if pref in (NotificationPreference.EMAIL, NotificationPreference.BOTH):
            if not self.email:
                raise ValueError("Email is required for email notifications")
        if pref in (NotificationPreference.SMS, NotificationPreference.BOTH):
            if not self.phone:
                raise ValueError("Phone number is required for SMS notifications")
        return self


class SubscriberResponse(BaseModel):
    id: UUID
    name: str
    email: str | None
    phone: str | None
    notification_preference: NotificationPreference
    confirmed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ConfirmResponse(BaseModel):
    message: str


class UnsubscribeResponse(BaseModel):
    message: str


class ResendConfirmationRequest(BaseModel):
    email: EmailStr


class ResendConfirmationResponse(BaseModel):
    message: str
