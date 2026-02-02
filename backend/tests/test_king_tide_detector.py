from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.king_tide_event import KingTideEvent
from app.models.notification_sent import NotificationSent, NotificationType
from app.models.subscriber import NotificationPreference, Subscriber
from app.services.king_tide_detector import detect_and_store_king_tides, send_alerts


@pytest.mark.asyncio
async def test_detect_stores_new_events(test_db):
    """Should store new king tide events from NOAA data."""
    mock_king_tides = [
        {"datetime": "2026-02-15 03:00", "height": 1.84, "type": "H"},
        {"datetime": "2026-02-16 03:30", "height": 1.92, "type": "H"},
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
        predicted_height=1.84,
        station_id="9414290",
    )
    test_db.add(existing)
    test_db.commit()

    mock_king_tides = [
        {"datetime": "2026-02-15 03:00", "height": 1.84, "type": "H"},
    ]

    with patch(
        "app.services.king_tide_detector.noaa.get_king_tides",
        new_callable=AsyncMock,
        return_value=mock_king_tides,
    ):
        events = await detect_and_store_king_tides(test_db)

    assert len(events) == 0
    assert test_db.query(KingTideEvent).count() == 1


@pytest.mark.asyncio
async def test_send_seven_day_alert(test_db):
    """Should send 7-day alerts and record notifications."""
    # Create a confirmed subscriber
    subscriber = Subscriber(
        name="Test",
        email="test@example.com",
        notification_preference=NotificationPreference.EMAIL,
        unsubscribe_token="token123",
        confirmed=True,
    )
    test_db.add(subscriber)

    # Create an event 6 days from now
    event = KingTideEvent(
        event_datetime=datetime.now(timezone.utc) + timedelta(days=6),
        predicted_height=1.84,
        station_id="9414290",
    )
    test_db.add(event)
    test_db.commit()

    with patch(
        "app.services.king_tide_detector.notification.send_king_tide_alert",
        new_callable=AsyncMock,
    ) as mock_send:
        await send_alerts(test_db)

    mock_send.assert_called_once()
    assert event.seven_day_alert_sent is True

    # Verify notification recorded
    notif = test_db.query(NotificationSent).first()
    assert notif is not None
    assert notif.notification_type == NotificationType.SEVEN_DAY_ALERT


@pytest.mark.asyncio
async def test_send_forty_eight_hour_reminder(test_db):
    """Should send 48-hour reminders."""
    subscriber = Subscriber(
        name="Test",
        email="test@example.com",
        notification_preference=NotificationPreference.EMAIL,
        unsubscribe_token="token456",
        confirmed=True,
    )
    test_db.add(subscriber)

    event = KingTideEvent(
        event_datetime=datetime.now(timezone.utc) + timedelta(days=2),
        predicted_height=1.92,
        station_id="9414290",
    )
    test_db.add(event)
    test_db.commit()

    with patch(
        "app.services.king_tide_detector.notification.send_king_tide_alert",
        new_callable=AsyncMock,
    ) as mock_send:
        await send_alerts(test_db)

    mock_send.assert_called_once()
    assert event.forty_eight_hour_alert_sent is True


@pytest.mark.asyncio
async def test_no_duplicate_notifications(test_db):
    """Should not re-send alerts that were already recorded."""
    subscriber = Subscriber(
        name="Test",
        email="test@example.com",
        notification_preference=NotificationPreference.EMAIL,
        unsubscribe_token="token789",
        confirmed=True,
    )
    test_db.add(subscriber)

    event = KingTideEvent(
        event_datetime=datetime.now(timezone.utc) + timedelta(days=6),
        predicted_height=1.84,
        station_id="9414290",
    )
    test_db.add(event)
    test_db.commit()

    # Record existing notification
    notif = NotificationSent(
        subscriber_id=subscriber.id,
        king_tide_event_id=event.id,
        notification_type=NotificationType.SEVEN_DAY_ALERT,
    )
    test_db.add(notif)
    test_db.commit()

    with patch(
        "app.services.king_tide_detector.notification.send_king_tide_alert",
        new_callable=AsyncMock,
    ) as mock_send:
        await send_alerts(test_db)

    mock_send.assert_not_called()
