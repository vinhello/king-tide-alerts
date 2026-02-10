import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

NOAA_BASE_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"


async def fetch_tide_predictions(
    days_ahead: int = 30,
    station_id: str | None = None,
) -> list[dict]:
    """Fetch high/low tide predictions from NOAA CO-OPS API.

    Returns only high tides (type == "H") with height relative to MHHW.
    """
    station = station_id or settings.NOAA_STATION_ID
    now = datetime.now(timezone.utc)
    begin = now.strftime("%Y%m%d")
    end = (now + timedelta(days=days_ahead)).strftime("%Y%m%d")

    params = {
        "product": "predictions",
        "begin_date": begin,
        "end_date": end,
        "datum": "MLLW",
        "station": station,
        "interval": "hilo",
        "units": "english",
        "time_zone": "lst_ldt",
        "format": "json",
        "application": "king_tide_alerts",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(NOAA_BASE_URL, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.error(f"NOAA API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching NOAA data: {e}")
            return []

    predictions = data.get("predictions", [])

    # Filter to high tides only
    high_tides = []
    for pred in predictions:
        if pred.get("type") == "H":
            high_tides.append(
                {
                    "datetime": pred["t"],
                    "height": float(pred["v"]),
                    "type": pred["type"],
                }
            )

    return high_tides


async def fetch_hourly_tide_predictions(
    days_ahead: int = 14,
    station_id: str | None = None,
) -> list[dict]:
    """Fetch hourly tide predictions from NOAA CO-OPS API.

    Returns one prediction per hour, used for chart display.
    """
    station = station_id or settings.NOAA_STATION_ID
    now = datetime.now(timezone.utc)
    begin = now.strftime("%Y%m%d")
    end = (now + timedelta(days=days_ahead)).strftime("%Y%m%d")

    params = {
        "product": "predictions",
        "begin_date": begin,
        "end_date": end,
        "datum": "MLLW",
        "station": station,
        "interval": "h",
        "units": "english",
        "time_zone": "lst_ldt",
        "format": "json",
        "application": "king_tide_alerts",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(NOAA_BASE_URL, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.error(f"NOAA API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching NOAA data: {e}")
            return []

    predictions = data.get("predictions", [])

    return [
        {
            "datetime": pred["t"],
            "height": float(pred["v"]),
        }
        for pred in predictions
    ]


async def get_king_tides(
    days_ahead: int = 30,
    threshold: float | None = None,
) -> list[dict]:
    """Return only high tides exceeding the king tide threshold."""
    thresh = threshold if threshold is not None else settings.KING_TIDE_THRESHOLD
    all_tides = await fetch_tide_predictions(days_ahead=days_ahead)
    return [t for t in all_tides if t["height"] > thresh]
