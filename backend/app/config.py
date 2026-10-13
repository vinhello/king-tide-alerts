import logging

from pydantic import model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

MIN_ADMIN_CREDENTIAL_LENGTH = 16


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://localhost/king_tide_alerts"
    RESEND_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    APP_URL: str = "http://localhost:5173"
    # San Francisco (Golden Gate). Nearest gauge with live observations and the
    # reference Marin County and Caltrans use for flooding at Manzanita.
    NOAA_STATION_ID: str = "9414290"
    KING_TIDE_THRESHOLD: float = 6.0
    KING_TIDE_HEIGHT: float = 6.5
    ADMIN_API_KEY: str = ""
    ADMIN_PASSWORD: str = ""
    ENVIRONMENT: str = "development"
    FEEDBACK_EMAIL: str = "info@kingtidealert.com"
    FEEDBACK_MAX_MESSAGE_LENGTH: int = 5000
    FEEDBACK_MAX_SUBJECT_LENGTH: int = 200
    DONATION_MIN_CENTS: int = 100
    DONATION_MAX_CENTS: int = 50000
    # Measured observed-minus-predicted water level shown to users (not a forecast).
    RESIDUAL_WINDOW_DAYS: int = 30
    RESIDUAL_CACHE_SECONDS: int = 3600
    # Dead man's switch for the daily job (healthchecks.io ping URL). Empty disables.
    HEALTHCHECK_PING_URL: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def validate_admin_credentials(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if not self.ADMIN_PASSWORD:
                raise ValueError("ADMIN_PASSWORD must be set in production")
            if len(self.ADMIN_PASSWORD) < MIN_ADMIN_CREDENTIAL_LENGTH:
                raise ValueError(
                    f"ADMIN_PASSWORD must be at least "
                    f"{MIN_ADMIN_CREDENTIAL_LENGTH} characters in production"
                )
        return self


settings = Settings()
