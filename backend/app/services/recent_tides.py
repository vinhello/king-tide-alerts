"""Measured water level for the past few days, next to the predictions for
the same hours.

Reporting only: the site draws both series so the gap between them is
visible. Nothing here forecasts anything.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.services import noaa

logger = logging.getLogger(__name__)

CACHE_SECONDS = 600
MAX_DAYS = 7
# NOAA returns local standard/daylight time for the gauge.
STATION_TZ = ZoneInfo("America/Los_Angeles")


@dataclass(frozen=True)
class RecentTides:
    observations: list[dict]
    predictions: list[dict]
    days: int
    as_of: str  # NOAA timestamp of the newest observation, "" when none


_cache: dict[int, tuple[float, RecentTides]] = {}


async def get_recent_tides(days: int) -> RecentTides:
    """Hourly observations and predictions for the trailing window, cached.

    Predictions are trimmed to the hours that have an observation, so the
    series line up. When NOAA returns nothing, the last good series is kept
    rather than showing an empty chart segment for a transient failure.
    """
    days = max(1, min(days, MAX_DAYS))
    now = time.monotonic()
    cached = _cache.get(days)
    if cached is not None and now - cached[0] < CACHE_SECONDS:
        return cached[1]

    end = datetime.now(STATION_TZ)
    begin = end - timedelta(days=days)
    begin_str, end_str = begin.strftime("%Y%m%d"), end.strftime("%Y%m%d")

    observations = await noaa.fetch_hourly_observations(begin_str, end_str)
    if not observations:
        logger.warning("No recent observations from NOAA; keeping the last series")
        return cached[1] if cached is not None else RecentTides([], [], days, "")

    newest = max(o["datetime"] for o in observations)
    predictions = [
        p
        for p in await noaa.fetch_hourly_predictions_between(begin_str, end_str)
        if p["datetime"] <= newest
    ]
    result = RecentTides(observations, predictions, days, newest)
    _cache[days] = (now, result)
    logger.info(
        f"Recent tides: {len(observations)} observed hours up to {newest}, "
        f"{len(predictions)} predicted"
    )
    return result


def clear_cache() -> None:
    """For tests."""
    _cache.clear()
