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


async def fetch_current_water_level(station_id: str | None = None) -> dict | None:
    """Fetch the latest water level observation from NOAA."""
    station = station_id or settings.NOAA_STATION_ID

    params = {
        "product": "water_level",
        "date": "latest",
        "datum": "MLLW",
        "station": station,
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
            logger.error(f"NOAA API error fetching water level: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching current water level: {e}")
            return None

    items = data.get("data", [])
    if not items:
        return None

    item = items[-1]
    try:
        return {"height": float(item["v"]), "timestamp": item["t"]}
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing water level data: {e}")
        return None


async def fetch_next_high_tide(station_id: str | None = None) -> dict | None:
    """Get the next upcoming high tide prediction.

    NOAA returns timestamps in local time (lst_ldt). We compare naive
    datetimes against each other to avoid timezone offset mismatches.
    """
    predictions = await fetch_tide_predictions(days_ahead=2, station_id=station_id)

    # NOAA lst_ldt returns local time strings; parse and compare as naive
    # to stay consistent with the timezone the API returns
    now_local_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    for pred in predictions:
        if pred["datetime"] > now_local_str:
            return {"datetime": pred["datetime"], "height": pred["height"]}

    return None
