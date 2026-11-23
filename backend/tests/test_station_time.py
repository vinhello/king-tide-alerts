import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.services import noaa
from app.utils.station_time import STATION_TZ, station_wall_clock_now


def test_wall_clock_now_is_the_pacific_reading_labelled_utc():
    instant = datetime(2026, 11, 24, 14, 0, tzinfo=timezone.utc)  # 6:00 AM PST
    with patch("app.utils.station_time.datetime") as mock_dt:
        mock_dt.now.side_effect = lambda tz=None: instant.astimezone(tz)
        reading = station_wall_clock_now()

    assert reading == datetime(2026, 11, 24, 6, 0, tzinfo=timezone.utc)


def test_next_high_tide_keeps_a_tide_later_this_morning():
    # 6:00 AM Pacific. The 10:05 AM tide is four hours away and must be the
    # next one; the server's UTC clock (14:00) would have skipped past it.
    predictions = [
        {"datetime": "2026-11-23 23:31", "height": 4.8},
        {"datetime": "2026-11-24 10:05", "height": 6.9},
        {"datetime": "2026-11-25 00:30", "height": 4.9},
    ]
    six_am = datetime(2026, 11, 24, 6, 0, tzinfo=STATION_TZ)
    with (
        patch("app.services.noaa.station_now", return_value=six_am),
        patch(
            "app.services.noaa.fetch_tide_predictions",
            new_callable=AsyncMock,
            return_value=predictions,
        ),
    ):
        result = asyncio.run(noaa.fetch_next_high_tide())

    assert result == {"datetime": "2026-11-24 10:05", "height": 6.9}
