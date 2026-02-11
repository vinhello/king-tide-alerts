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
