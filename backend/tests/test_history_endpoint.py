import uuid
from datetime import datetime, timedelta, timezone

from app.models.king_tide_event import KingTideEvent
from app.models.notification_sent import NotificationSent, NotificationType
from app.models.subscriber import NotificationPreference, Subscriber


def _make_subscriber(db):
    subscriber = Subscriber(
        id=uuid.uuid4(),
        name="Test User",
        email=f"test-{uuid.uuid4()}@example.com",
        notification_preference=NotificationPreference.EMAIL,
        unsubscribe_token=str(uuid.uuid4()),
        confirmed=True,
    )
    db.add(subscriber)
    db.flush()
    return subscriber


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


def test_history_returns_empty_list(client):
    response = client.get("/api/tides/history")
    assert response.status_code == 200
    data = response.json()
    assert data["events"] == []
    assert data["total"] == 0


def test_history_returns_events_with_notification_count(client, test_db):
    subscriber = _make_subscriber(test_db)
    future = datetime.now(timezone.utc) + timedelta(days=5)
    event = _make_event(test_db, future)

    notification = NotificationSent(
        id=uuid.uuid4(),
        subscriber_id=subscriber.id,
        king_tide_event_id=event.id,
        notification_type=NotificationType.SEVEN_DAY_ALERT,
    )
    test_db.add(notification)
    test_db.commit()

    response = client.get("/api/tides/history")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["events"]) == 1
    assert data["events"][0]["notifications_sent"] == 1


def test_history_filter_upcoming(client, test_db):
    past = datetime.now(timezone.utc) - timedelta(days=5)
    future = datetime.now(timezone.utc) + timedelta(days=5)
    _make_event(test_db, past)
    _make_event(test_db, future)
    test_db.commit()

    response = client.get("/api/tides/history?filter=upcoming")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["events"]) == 1
    assert data["events"][0]["event_datetime"] > datetime.now(timezone.utc).isoformat()


def test_history_filter_past(client, test_db):
    past = datetime.now(timezone.utc) - timedelta(days=5)
    future = datetime.now(timezone.utc) + timedelta(days=5)
    _make_event(test_db, past)
    _make_event(test_db, future)
    test_db.commit()

    response = client.get("/api/tides/history?filter=past")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["events"]) == 1
    assert data["events"][0]["event_datetime"] < datetime.now(timezone.utc).isoformat()


def test_history_pagination(client, test_db):
    base = datetime.now(timezone.utc) + timedelta(days=1)
    for i in range(3):
        _make_event(test_db, base + timedelta(days=i))
    test_db.commit()

    response = client.get("/api/tides/history?per_page=2&page=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["events"]) == 2
