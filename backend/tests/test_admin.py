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
            headers={"x-admin-password": "test-password"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["scheduler_running"] is False
    assert data["environment"] == "development"


def test_health_rejected_without_key(client):
    """GET /api/admin/health without password should return 401."""
    response = client.get("/api/admin/health")
    assert response.status_code == 401


def test_health_rejected_wrong_key(client):
    """GET /api/admin/health with wrong API key should return 403."""
    response = client.get(
        "/api/admin/health",
        headers={"x-admin-password": "wrong-password"},
    )
    assert response.status_code == 403


def test_stats_empty(client):
    """GET /api/admin/stats with no subscribers should return zeros."""
    response = client.get(
        "/api/admin/stats",
        headers={"x-admin-password": "test-password"},
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
        headers={"x-admin-password": "test-password"},
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
        headers={"x-admin-password": "test-password"},
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
        headers={"x-admin-password": "test-password"},
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
        station_id="9414290",
    )
    past_event = KingTideEvent(
        event_datetime=datetime.now(timezone.utc) - timedelta(days=5),
        predicted_height=6.5,
        station_id="9414290",
    )
    test_db.add_all([future_event, past_event])
    test_db.commit()

    response = client.get(
        "/api/admin/events",
        headers={"x-admin-password": "test-password"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["predicted_height"] == 6.8


def test_test_alert_sends_only_to_explicit_recipient(client, test_db):
    """POST /api/admin/test-alert sends to the given address and nobody else."""
    _create_confirmed_subscriber(test_db)
    test_db.add(
        Subscriber(
            name="Another", email="another@example.com",
            notification_preference="email", unsubscribe_token="tok-another", confirmed=True,
        )
    )
    test_db.commit()

    with patch(
        "app.routers.admin.send_king_tide_alert", new_callable=AsyncMock
    ) as mock_send:
        response = client.post(
            "/api/admin/test-alert?to=vince@example.com",
            headers={"x-admin-password": "test-password"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Test alert sent to vince@example.com"
    mock_send.assert_called_once()
    recipient = mock_send.call_args.kwargs["subscriber"]
    assert recipient.email == "vince@example.com"

    # Nothing persisted: no event, no notification record, no new subscriber
    assert test_db.query(KingTideEvent).count() == 0
    assert test_db.query(NotificationSent).count() == 0
    assert test_db.query(Subscriber).count() == 2


def test_test_alert_requires_recipient(client, test_db):
    """POST /api/admin/test-alert without `to` is refused and sends nothing."""
    _create_confirmed_subscriber(test_db)
    with patch(
        "app.routers.admin.send_king_tide_alert", new_callable=AsyncMock
    ) as mock_send:
        response = client.post(
            "/api/admin/test-alert",
            headers={"x-admin-password": "test-password"},
        )
    assert response.status_code == 422
    mock_send.assert_not_called()


def test_test_alert_rejects_invalid_recipient(client):
    response = client.post(
        "/api/admin/test-alert?to=not-an-email",
        headers={"x-admin-password": "test-password"},
    )
    assert response.status_code == 422


def test_test_alert_wrong_key(client):
    """POST /api/admin/test-alert with wrong API key should return 403."""
    response = client.post(
        "/api/admin/test-alert",
        headers={"x-admin-password": "wrong-password"},
    )
    assert response.status_code == 403


def test_test_alert_height_too_low(client):
    """POST /api/admin/test-alert with height below minimum should return 422."""
    response = client.post(
        "/api/admin/test-alert?to=a@b.com&height=4.0",
        headers={"x-admin-password": "test-password"},
    )
    assert response.status_code == 422


def test_test_alert_height_too_high(client):
    """POST /api/admin/test-alert with height above maximum should return 422."""
    response = client.post(
        "/api/admin/test-alert?to=a@b.com&height=25.0",
        headers={"x-admin-password": "test-password"},
    )
    assert response.status_code == 422


def test_test_alert_days_until_too_low(client):
    """POST /api/admin/test-alert with days_until below minimum should return 422."""
    response = client.post(
        "/api/admin/test-alert?to=a@b.com&days_until=0",
        headers={"x-admin-password": "test-password"},
    )
    assert response.status_code == 422


def test_test_alert_days_until_too_high(client):
    """POST /api/admin/test-alert with days_until above maximum should return 422."""
    response = client.post(
        "/api/admin/test-alert?to=a@b.com&days_until=31",
        headers={"x-admin-password": "test-password"},
    )
    assert response.status_code == 422


def test_alert_preview_reports_plan_without_sending(client, test_db):
    """GET /api/admin/alerts/preview describes the run and sends nothing."""
    from datetime import timedelta

    _create_confirmed_subscriber(test_db)
    event_dt = datetime.now(timezone.utc) + timedelta(days=2)
    event = KingTideEvent(event_datetime=event_dt, predicted_height=6.7, station_id="9414290")
    test_db.add(event)
    test_db.commit()

    with patch(
        "app.services.notification.send_king_tide_alert", new_callable=AsyncMock
    ) as mock_send:
        response = client.get(
            "/api/admin/alerts/preview",
            headers={"x-admin-password": "test-password"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["dry_run"] is True
    assert data["subscriber_count"] == 1
    assert len(data["alerts"]) == 1
    assert data["alerts"][0]["notification_type"] == "forty_eight_hour_reminder"
    assert data["alerts"][0]["recipient_count"] == 1
    assert "King Tide" in data["sample_subject"]
    assert "Unsubscribe" in data["sample_email_html"]

    mock_send.assert_not_called()
    test_db.refresh(event)
    assert event.forty_eight_hour_alert_sent is False
    assert test_db.query(NotificationSent).count() == 0


def test_alert_preview_with_nothing_due(client, test_db):
    _create_confirmed_subscriber(test_db)
    response = client.get(
        "/api/admin/alerts/preview",
        headers={"x-admin-password": "test-password"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["alerts"] == []
    assert data["sample_email_html"] is None



def test_stats_buckets_exclude_unsubscribed(client, test_db):
    _create_confirmed_subscriber(test_db, email="active@example.com")
    gone = _create_confirmed_subscriber(test_db, email="gone@example.com")
    gone.unsubscribed_at = datetime.now(timezone.utc)
    test_db.add(
        Subscriber(
            name="Pending", email="pending@example.com", notification_preference="email",
            unsubscribe_token="tok-pending", confirmed=False,
        )
    )
    test_db.commit()

    response = client.get("/api/admin/stats", headers={"x-admin-password": "test-password"})
    data = response.json()
    assert data["total"] == 2
    assert data["confirmed"] == 1
    assert data["unconfirmed"] == 1
    assert data["unsubscribed"] == 1
