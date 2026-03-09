from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://localhost/king_tide_alerts"
    RESEND_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    APP_URL: str = "http://localhost:5173"
    NOAA_STATION_ID: str = "9414806"
    KING_TIDE_THRESHOLD: float = 6.0
    KING_TIDE_HEIGHT: float = 6.5
    ADMIN_API_KEY: str = ""
    ADMIN_PASSWORD: str = ""
    ENVIRONMENT: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
