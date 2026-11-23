"""The station's clock.

NOAA predictions are requested in the station's local time, and tide times
are kept with that wall-clock reading (labelled UTC in the database). Anything
that asks "has this tide happened yet?" or "what is today's date at the
station?" must therefore use the station's clock, not the server's UTC clock,
or it runs seven to eight hours ahead.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

STATION_TZ = ZoneInfo("America/Los_Angeles")


def station_now() -> datetime:
    """The current time at the station, timezone-aware."""
    return datetime.now(STATION_TZ)


def station_wall_clock_now() -> datetime:
    """The station's current wall-clock reading in the stored convention.

    Comparable with KingTideEvent.event_datetime, which holds the local
    reading labelled as UTC.
    """
    return station_now().replace(tzinfo=timezone.utc)
