from pydantic import BaseModel, EmailStr, Field, field_validator

from app.config import settings


class FeedbackRequest(BaseModel):
    message: str = Field(
        min_length=1, max_length=settings.FEEDBACK_MAX_MESSAGE_LENGTH
    )
    subject: str | None = Field(
        default=None, max_length=settings.FEEDBACK_MAX_SUBJECT_LENGTH
    )
    email: EmailStr | None = None
    # Honeypot. Hidden in the UI; real visitors leave it empty, bots fill it.
    website: str | None = Field(default=None, max_length=200)

    @field_validator("message", "subject", "email", "website", mode="before")
    @classmethod
    def strip_and_blank_to_none(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped if stripped else None
        return value


class FeedbackResponse(BaseModel):
    message: str
