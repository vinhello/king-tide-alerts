"""Measured difference between observed and predicted water level.

Reports how far the water at the configured gauge has actually run above or
below NOAA's astronomical predictions over a trailing window. This is a
measurement of the recent past, not a forecast, and is worded that way
everywhere it is shown.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.services import noaa

logger = logging.getLogger(__name__)

# Fewer matched hours than this and the mean is not worth showing.
MIN_SAMPLE_HOURS = 48


@dataclass(frozen=True)
class ResidualSummary:
    mean_residual_ft: float
    sample_hours: int
    window_days: int
    as_of: str  # local date of the newest observation used, YYYY-MM-DD


_cached_summary: ResidualSummary | None = None
_cached_at: float = 0.0


def compute_residual(
    observations: list[dict], predictions: list[dict], window_days: int
) -> ResidualSummary | None:
    """Mean of observed minus predicted over timestamps present in both series."""
    predicted = {p["datetime"]: p["height"] for p in predictions}
    diffs = []
    newest = ""
    for obs in observations:
        stamp = obs["datetime"]
        if stamp in predicted:
            diffs.append(obs["height"] - predicted[stamp])
            if stamp > newest:
                newest = stamp
    if len(diffs) < MIN_SAMPLE_HOURS:
        return None
    return ResidualSummary(
        mean_residual_ft=round(sum(diffs) / len(diffs), 2),
        sample_hours=len(diffs),
        window_days=window_days,
        as_of=newest[:10],
    )


async def get_residual_summary() -> ResidualSummary | None:
    """Trailing-window residual at the configured station, cached in memory.

    Returns None when NOAA data is unavailable or too sparse; callers omit
    the figure rather than show a guess.
    """
    global _cached_summary, _cached_at

    now = time.monotonic()
    if _cached_summary is not None and now - _cached_at < settings.RESIDUAL_CACHE_SECONDS:
        return _cached_summary

    window_days = settings.RESIDUAL_WINDOW_DAYS
    end = datetime.now(timezone.utc)
    begin = end - timedelta(days=window_days)
    begin_str, end_str = begin.strftime("%Y%m%d"), end.strftime("%Y%m%d")

    observations = await noaa.fetch_hourly_observations(begin_str, end_str)
    predictions = await noaa.fetch_hourly_predictions_between(begin_str, end_str)
    summary = compute_residual(observations, predictions, window_days)

    if summary is None:
        logger.warning("Residual unavailable: insufficient matched NOAA data")
        # Keep any previous summary rather than caching a failure.
        return _cached_summary

    _cached_summary = summary
    _cached_at = now
    logger.info(
        f"Residual over {summary.window_days} days: {summary.mean_residual_ft:+.2f} ft "
        f"from {summary.sample_hours} matched hours"
    )
    return summary


def clear_cache() -> None:
    """For tests."""
    global _cached_summary, _cached_at
    _cached_summary = None
    _cached_at = 0.0
