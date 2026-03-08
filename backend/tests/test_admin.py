from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from app.models.king_tide_event import KingTideEvent
from app.models.notification_sent import NotificationSent, NotificationType
from app.models.subscriber import Subscriber


def _create_confirmed_subscriber(db, email="alert@example.com", name="Test User"):
    subscriber = Subscriber(
        name=name,
        email=email,
        notification_preference="email",
        unsubscribe_token=f"token-{email}",
        confirmed=True,
    )
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    return subscriber


def test_health_returns_status(client):
    """GET /api/admin/health should return system health info."""
    with patch("app.services.scheduler.scheduler") as mock_scheduler:
        mock_scheduler.running = False
        response = client.get(
            "/api/admin/health",
            headers={"x-api-key": "test-key"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["scheduler_running"] is False
    assert data["environment"] == "development"


def test_health_rejected_without_key(client):
    """GET /api/admin/health without API key should return 422."""
    response = client.get("/api/admin/health")
    assert response.status_code == 422


def test_health_rejected_wrong_key(client):
    """GET /api/admin/health with wrong API key should return 403."""
    response = client.get(
        "/api/admin/health",
        headers={"x-api-key": "wrong-key"},
    )
    assert response.status_code == 403


def test_stats_empty(client):
    """GET /api/admin/stats with no subscribers should return zeros."""
    response = client.get(
        "/api/admin/stats",
        headers={"x-api-key": "test-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["confirmed"] == 0
    assert data["unconfirmed"] == 0


def test_stats_with_data(client, test_db):
    """GET /api/admin/stats should return correct counts."""
    _create_confirmed_subscriber(test_db, "a@test.com", "A")
    _create_confirmed_subscriber(test_db, "b@test.com", "B")

    # Unconfirmed subscriber
    unsub = Subscriber(
        name="C",
        email="c@test.com",
        notification_preference="sms",
        unsubscribe_token="token-c",
        confirmed=False,
    )
    test_db.add(unsub)
    test_db.commit()

    response = client.get(
        "/api/admin/stats",
        headers={"x-api-key": "test-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["confirmed"] == 2
    assert data["unconfirmed"] == 1
    assert data["email_only"] == 2
    assert data["sms_only"] == 1


def test_notifications_empty(client):
    """GET /api/admin/notifications with no data should return zeros."""
    response = client.get(
        "/api/admin/notifications",
        headers={"x-api-key": "test-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_sent"] == 0
    assert data["recent"] == []


def test_notifications_with_data(client, test_db):
    """GET /api/admin/notifications should return correct counts and recent items."""
    subscriber = _create_confirmed_subscriber(test_db)

    notification = NotificationSent(
        subscriber_id=subscriber.id,
        notification_type=NotificationType.SEVEN_DAY_ALERT,
    )
    test_db.add(notification)
    test_db.commit()

    response = client.get(
        "/api/admin/notifications",
        headers={"x-api-key": "test-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_sent"] == 1
    assert data["seven_day_alerts"] == 1
    assert len(data["recent"]) == 1
    assert data["recent"][0]["subscriber_name"] == "Test User"


def test_events_upcoming(client, test_db):
    """GET /api/admin/events should return only future events."""
    future_event = KingTideEvent(
        event_datetime=datetime.now(timezone.utc) + timedelta(days=5),
        predicted_height=6.8,
        station_id="9414806",
    )
    past_event = KingTideEvent(
        event_datetime=datetime.now(timezone.utc) - timedelta(days=5),
        predicted_height=6.5,
        station_id="9414806",
    )
    test_db.add_all([future_event, past_event])
    test_db.commit()

    response = client.get(
        "/api/admin/events",
        headers={"x-api-key": "test-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["predicted_height"] == 6.8


def test_test_alert_sends(client, test_db):
    """POST /api/admin/test-alert should send alerts to confirmed subscribers."""
    _create_confirmed_subscriber(test_db)

    with patch(
        "app.routers.admin.send_king_tide_alert", new_callable=AsyncMock
    ) as mock_send:
        response = client.post(
            "/api/admin/test-alert",
            headers={"x-api-key": "test-key"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Test alert sent to 1 subscriber(s)"
    mock_send.assert_called_once()

    # Verify no KingTideEvent was persisted
    assert test_db.query(KingTideEvent).count() == 0


def test_test_alert_no_subscribers(client):
    """POST /api/admin/test-alert should return 404 if no confirmed subscribers."""
    response = client.post(
        "/api/admin/test-alert",
        headers={"x-api-key": "test-key"},
    )
    assert response.status_code == 404


def test_test_alert_wrong_key(client):
    """POST /api/admin/test-alert with wrong API key should return 403."""
    response = client.post(
        "/api/admin/test-alert",
        headers={"x-api-key": "wrong-key"},
    )
    assert response.status_code == 403
