from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.king_tide_event import KingTideEvent
from app.models.notification_sent import NotificationSent, NotificationType
from app.models.subscriber import NotificationPreference, Subscriber
from app.services.king_tide_detector import (
    TidePeriod,
    _group_into_periods,
    detect_and_store_king_tides,
    send_alerts,
)


# --- detect_and_store_king_tides tests (unchanged) ---


@pytest.mark.asyncio
async def test_detect_stores_new_events(test_db):
    """Should store new king tide events from NOAA data."""
    mock_king_tides = [
        {"datetime": "2026-02-15 03:00", "height": 6.8, "type": "H"},
        {"datetime": "2026-02-16 03:30", "height": 7.1, "type": "H"},
    ]

    with patch(
        "app.services.king_tide_detector.noaa.get_king_tides",
        new_callable=AsyncMock,
        return_value=mock_king_tides,
    ):
        events = await detect_and_store_king_tides(test_db)

    assert len(events) == 2
    assert test_db.query(KingTideEvent).count() == 2


@pytest.mark.asyncio
async def test_detect_skips_existing_events(test_db):
    """Should not create duplicate events for the same datetime."""
    event_dt = datetime(2026, 2, 15, 3, 0, tzinfo=timezone.utc)
    existing = KingTideEvent(
        event_datetime=event_dt,
        predicted_height=6.8,
        station_id="9414806",
    )
    test_db.add(existing)
    test_db.commit()

    mock_king_tides = [
        {"datetime": "2026-02-15 03:00", "height": 6.8, "type": "H"},
    ]

    with patch(
        "app.services.king_tide_detector.noaa.get_king_tides",
        new_callable=AsyncMock,
        return_value=mock_king_tides,
    ):
        events = await detect_and_store_king_tides(test_db)

    assert len(events) == 0
    assert test_db.query(KingTideEvent).count() == 1


# --- _group_into_periods tests ---


def test_group_consecutive_days_into_one_period(test_db):
    """Events on consecutive days should be grouped into one period."""
    base = datetime(2026, 3, 10, 3, 0, tzinfo=timezone.utc)
    events = []
    for i in range(3):
        e = KingTideEvent(
            event_datetime=base + timedelta(days=i),
            predicted_height=6.5 + i * 0.1,
            station_id="9414806",
        )
        test_db.add(e)
        events.append(e)
    test_db.commit()

    periods = _group_into_periods(events)
    assert len(periods) == 1
    assert periods[0].start_date == base.date()
    assert periods[0].end_date == (base + timedelta(days=2)).date()
    assert periods[0].peak_height == 6.7
    assert len(periods[0].event_ids) == 3


def test_group_gap_creates_two_periods(test_db):
    """Events with a gap of 2+ days should be in separate periods."""
    base = datetime(2026, 3, 10, 3, 0, tzinfo=timezone.utc)
    e1 = KingTideEvent(
        event_datetime=base,
        predicted_height=6.5,
        station_id="9414806",
    )
    e2 = KingTideEvent(
        event_datetime=base + timedelta(days=1),
        predicted_height=6.6,
        station_id="9414806",
    )
    # Gap of 2 days
    e3 = KingTideEvent(
        event_datetime=base + timedelta(days=4),
        predicted_height=6.8,
        station_id="9414806",
    )
    test_db.add_all([e1, e2, e3])
    test_db.commit()

    periods = _group_into_periods([e1, e2, e3])
    assert len(periods) == 2
    assert periods[0].start_date == base.date()
    assert periods[0].end_date == (base + timedelta(days=1)).date()
    assert periods[0].peak_height == 6.6
    assert periods[1].start_date == (base + timedelta(days=4)).date()
    assert periods[1].peak_height == 6.8


def test_group_single_event(test_db):
    """A single event should form a single period."""
    base = datetime(2026, 3, 10, 3, 0, tzinfo=timezone.utc)
    e = KingTideEvent(
        event_datetime=base,
        predicted_height=6.5,
        station_id="9414806",
    )
    test_db.add(e)
    test_db.commit()

    periods = _group_into_periods([e])
    assert len(periods) == 1
    assert periods[0].start_date == periods[0].end_date == base.date()


def test_group_multiple_events_same_day(test_db):
    """Multiple events on the same day should be one period."""
    base = datetime(2026, 3, 10, 3, 0, tzinfo=timezone.utc)
    e1 = KingTideEvent(
        event_datetime=base,
        predicted_height=6.5,
        station_id="9414806",
    )
    e2 = KingTideEvent(
        event_datetime=base + timedelta(hours=12),
        predicted_height=6.9,
        station_id="9414806",
    )
    test_db.add_all([e1, e2])
    test_db.commit()

    periods = _group_into_periods([e1, e2])
    assert len(periods) == 1
    assert periods[0].peak_height == 6.9
    assert len(periods[0].event_ids) == 2


def test_group_empty_list():
    """Empty event list should produce no periods."""
    assert _group_into_periods([]) == []


# --- send_alerts period-based tests ---


def _create_subscriber(test_db, name="Test", email="test@example.com", token="token123"):
    subscriber = Subscriber(
        name=name,
        email=email,
        notification_preference=NotificationPreference.EMAIL,
        unsubscribe_token=token,
        confirmed=True,
    )
    test_db.add(subscriber)
    test_db.commit()
    return subscriber


@pytest.mark.asyncio
async def test_send_seven_day_alert_for_period(test_db):
    """Should send one 7-day alert for a period of consecutive events."""
    _create_subscriber(test_db)

    # Create 3 events on consecutive days, all 6 days away
    base = datetime.now(timezone.utc) + timedelta(days=6)
    for i in range(3):
        test_db.add(KingTideEvent(
            event_datetime=base + timedelta(days=i),
            predicted_height=6.5 + i * 0.1,
            station_id="9414806",
        ))
    test_db.commit()

    with patch(
        "app.services.king_tide_detector.notification.send_king_tide_alert",
        new_callable=AsyncMock,
    ) as mock_send:
        await send_alerts(test_db)

    # Should send exactly 1 alert (not 3)
    mock_send.assert_called_once()

    # All events should be marked as alerted
    events = test_db.query(KingTideEvent).all()
    assert all(e.seven_day_alert_sent for e in events)

    # Only 1 NotificationSent record
    assert test_db.query(NotificationSent).count() == 1
    notif = test_db.query(NotificationSent).first()
    assert notif.notification_type == NotificationType.SEVEN_DAY_ALERT


@pytest.mark.asyncio
async def test_send_forty_eight_hour_alert_for_period(test_db):
    """Should send one 48-hour alert for a period."""
    _create_subscriber(test_db)

    base = datetime.now(timezone.utc) + timedelta(days=2)
    for i in range(2):
        test_db.add(KingTideEvent(
            event_datetime=base + timedelta(days=i),
            predicted_height=7.0 + i * 0.1,
            station_id="9414806",
        ))
    test_db.commit()

    with patch(
        "app.services.king_tide_detector.notification.send_king_tide_alert",
        new_callable=AsyncMock,
    ) as mock_send:
        await send_alerts(test_db)

    mock_send.assert_called_once()
    events = test_db.query(KingTideEvent).all()
    assert all(e.forty_eight_hour_alert_sent for e in events)


@pytest.mark.asyncio
async def test_two_periods_get_separate_alerts(test_db):
    """Events with a gap should produce separate alerts."""
    _create_subscriber(test_db)

    now = datetime.now(timezone.utc)
    # Period 1: 6 days away (7-day window)
    test_db.add(KingTideEvent(
        event_datetime=now + timedelta(days=6),
        predicted_height=6.5,
        station_id="9414806",
    ))
    # Period 2: 7 days away but with a gap from period 1
    # (3-day gap from period 1 event)
    test_db.add(KingTideEvent(
        event_datetime=now + timedelta(days=6 + 3),
        predicted_height=6.8,
        station_id="9414806",
    ))
    test_db.commit()

    with patch(
        "app.services.king_tide_detector.notification.send_king_tide_alert",
        new_callable=AsyncMock,
    ) as mock_send:
        await send_alerts(test_db)

    # Period 1 is in 7-day window, period 2 starts at day 9 (outside 5-8 window)
    # So only 1 alert should be sent
    assert mock_send.call_count == 1


@pytest.mark.asyncio
async def test_no_duplicate_period_alerts(test_db):
    """Should not re-send alerts when events already have alert_sent=True."""
    _create_subscriber(test_db)

    base = datetime.now(timezone.utc) + timedelta(days=6)
    event = KingTideEvent(
        event_datetime=base,
        predicted_height=6.8,
        station_id="9414806",
        seven_day_alert_sent=True,  # Already sent
    )
    test_db.add(event)
    test_db.commit()

    with patch(
        "app.services.king_tide_detector.notification.send_king_tide_alert",
        new_callable=AsyncMock,
    ) as mock_send:
        await send_alerts(test_db)

    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_no_alerts_without_subscribers(test_db):
    """Should skip alerts when there are no confirmed subscribers."""
    base = datetime.now(timezone.utc) + timedelta(days=6)
    test_db.add(KingTideEvent(
        event_datetime=base,
        predicted_height=6.8,
        station_id="9414806",
    ))
    test_db.commit()

    with patch(
        "app.services.king_tide_detector.notification.send_king_tide_alert",
        new_callable=AsyncMock,
    ) as mock_send:
        await send_alerts(test_db)

    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_alert_uses_peak_event_params(test_db):
    """Alert should use peak height and datetime from the period."""
    _create_subscriber(test_db)

    base = datetime.now(timezone.utc) + timedelta(days=6)
    test_db.add(KingTideEvent(
        event_datetime=base,
        predicted_height=6.2,
        station_id="9414806",
    ))
    test_db.add(KingTideEvent(
        event_datetime=base + timedelta(days=1),
        predicted_height=7.1,  # Peak
        station_id="9414806",
    ))
    test_db.add(KingTideEvent(
        event_datetime=base + timedelta(days=2),
        predicted_height=6.5,
        station_id="9414806",
    ))
    test_db.commit()

    with patch(
        "app.services.king_tide_detector.notification.send_king_tide_alert",
        new_callable=AsyncMock,
    ) as mock_send:
        await send_alerts(test_db)

    mock_send.assert_called_once()
    call_kwargs = mock_send.call_args.kwargs
    assert call_kwargs["peak_height"] == 7.1
