import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from app.models.king_tide_event import KingTideEvent


def _make_event(db, event_datetime, height=6.8):
    event = KingTideEvent(
        id=uuid.uuid4(),
        event_datetime=event_datetime,
        predicted_height=height,
        station_id="9414806",
        seven_day_alert_sent=False,
        forty_eight_hour_alert_sent=False,
    )
    db.add(event)
    db.flush()
    return event


def test_calendar_returns_ics_content_type(client, test_db):
    future = datetime.now(timezone.utc) + timedelta(days=5)
    _make_event(test_db, future)
    test_db.commit()

    response = client.get("/api/tides/calendar.ics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")


def test_calendar_contains_events(client, test_db):
    base = datetime.now(timezone.utc) + timedelta(days=3)
    _make_event(test_db, base)
    _make_event(test_db, base + timedelta(days=2))
    test_db.commit()

    response = client.get("/api/tides/calendar.ics")
    assert response.status_code == 200
    assert response.text.count("BEGIN:VEVENT") == 2


def test_calendar_content_disposition(client, test_db):
    future = datetime.now(timezone.utc) + timedelta(days=5)
    _make_event(test_db, future)
    test_db.commit()

    response = client.get("/api/tides/calendar.ics")
    assert response.status_code == 200
    assert (
        response.headers["content-disposition"]
        == "attachment; filename=king-tide-alerts.ics"
    )


def test_calendar_empty_db_falls_back_to_noaa(client, test_db):
    mock_tides = [
        {"datetime": "2026-04-01 08:00", "height": 6.9},
        {"datetime": "2026-04-02 09:00", "height": 6.7},
    ]

    with patch(
        "app.routers.tides.get_king_tides",
        new_callable=AsyncMock,
        return_value=mock_tides,
    ):
        response = client.get("/api/tides/calendar.ics")

    assert response.status_code == 200
    assert response.text.count("BEGIN:VEVENT") == 2
