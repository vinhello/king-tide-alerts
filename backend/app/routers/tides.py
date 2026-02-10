from fastapi import APIRouter, Query

from app.config import settings
from app.schemas.tide import TidePrediction, UpcomingTidesResponse
from app.services.noaa import fetch_all_tide_predictions

router = APIRouter(prefix="/api/tides", tags=["tides"])


@router.get("/upcoming", response_model=UpcomingTidesResponse)
async def upcoming_tides(days: int = Query(default=14, ge=1, le=30)):
    predictions = await fetch_all_tide_predictions(days_ahead=days)

    tide_predictions = [
        TidePrediction(
            datetime=p["datetime"],
            height=p["height"],
            type=p["type"],
            is_king_tide=p["height"] >= settings.KING_TIDE_HEIGHT,
        )
        for p in predictions
    ]

    return UpcomingTidesResponse(
        predictions=tide_predictions,
        threshold=settings.KING_TIDE_THRESHOLD,
        station_id=settings.NOAA_STATION_ID,
    )
