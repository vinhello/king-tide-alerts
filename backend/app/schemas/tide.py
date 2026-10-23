from pydantic import BaseModel


class TidePrediction(BaseModel):
    datetime: str
    height: float
    type: str = ""
    is_king_tide: bool


class UpcomingTidesResponse(BaseModel):
    predictions: list[TidePrediction]
    threshold: float
    king_tide_height: float
    station_id: str


class HistoryEvent(BaseModel):
    id: str
    event_datetime: str
    predicted_height: float
    is_king_tide: bool
    seven_day_alert_sent: bool
    forty_eight_hour_alert_sent: bool
    notifications_sent: int


class HistoryResponse(BaseModel):
    events: list[HistoryEvent]
    total: int
    threshold: float
    king_tide_height: float


class CurrentTideStatus(BaseModel):
    current_height: float
    current_time: str
    next_high_tide_time: str | None
    next_high_tide_height: float | None
    hours_until_high_tide: float | None
    status: str
    threshold: float


class TidePoint(BaseModel):
    datetime: str
    height: float


class ObservedTidesResponse(BaseModel):
    """Measured water levels for the past few days and the predictions for
    the same hours. Empty lists when the gauge record is unavailable."""

    observations: list[TidePoint]
    predictions: list[TidePoint]
    days: int
    as_of: str
    station_id: str
