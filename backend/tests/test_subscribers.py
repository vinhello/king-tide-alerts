from unittest.mock import patch, AsyncMock

from app.models.subscriber import Subscriber


def test_subscribe_email_success(client, test_db):
    """POST valid email subscriber should return 201 and create DB row."""
    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        response = client.post(
            "/api/subscribe",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "notification_preference": "email",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test User"
    assert data["email"] == "test@example.com"
    assert data["confirmed"] is False

    # Verify DB row
    subscriber = test_db.query(Subscriber).filter_by(email="test@example.com").first()
    assert subscriber is not None
    assert subscriber.name == "Test User"


def test_subscribe_sms_success(client, test_db):
    """POST valid phone subscriber should return 201."""
    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        response = client.post(
            "/api/subscribe",
            json={
                "name": "SMS User",
                "phone": "+14155551234",
                "notification_preference": "sms",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["phone"] == "+14155551234"


def test_subscribe_duplicate_email_rejected(client, test_db):
    """Duplicate email should return 400."""
    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        client.post(
            "/api/subscribe",
            json={
                "name": "First",
                "email": "dupe@example.com",
                "notification_preference": "email",
            },
        )
        response = client.post(
            "/api/subscribe",
            json={
                "name": "Second",
                "email": "dupe@example.com",
                "notification_preference": "email",
            },
        )

    assert response.status_code == 400
    assert "already subscribed" in response.json()["detail"].lower()


def test_subscribe_missing_email_for_email_pref(client):
    """Email preference without email should fail validation."""
    response = client.post(
        "/api/subscribe",
        json={
            "name": "No Email",
            "notification_preference": "email",
        },
    )
    assert response.status_code == 422


def test_confirm_subscription(client, test_db):
    """Confirm via token should set confirmed=True."""
    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        client.post(
            "/api/subscribe",
            json={
                "name": "Confirm Me",
                "email": "confirm@example.com",
                "notification_preference": "email",
            },
        )

    # Get the token from the DB
    subscriber = (
        test_db.query(Subscriber).filter_by(email="confirm@example.com").first()
    )
    assert subscriber is not None
    assert subscriber.confirmed is False

    response = client.get(f"/api/confirm/{subscriber.unsubscribe_token}")
    assert response.status_code == 200
    assert "confirmed" in response.json()["message"].lower()

    test_db.refresh(subscriber)
    assert subscriber.confirmed is True


def test_unsubscribe(client, test_db):
    """Unsubscribe via token should delete subscriber."""
    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        client.post(
            "/api/subscribe",
            json={
                "name": "Unsub Me",
                "email": "unsub@example.com",
                "notification_preference": "email",
            },
        )

    subscriber = test_db.query(Subscriber).filter_by(email="unsub@example.com").first()
    token = subscriber.unsubscribe_token

    response = client.get(f"/api/unsubscribe/{token}")
    assert response.status_code == 200
    assert "unsubscribed" in response.json()["message"].lower()

    # Verify deleted
    assert test_db.query(Subscriber).filter_by(email="unsub@example.com").first() is None


def test_invalid_token_returns_404(client):
    """Confirm/unsubscribe with bad token should return 404."""
    response = client.get("/api/confirm/invalid-token-xyz")
    assert response.status_code == 404

    response = client.get("/api/unsubscribe/invalid-token-xyz")
    assert response.status_code == 404


def test_test_alert_sends_to_confirmed_subscribers(client, test_db):
    """POST /api/admin/test-alert should send alerts to confirmed subscribers."""
    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        client.post(
            "/api/subscribe",
            json={
                "name": "Alert Test",
                "email": "alert@example.com",
                "notification_preference": "email",
            },
        )

    # Confirm the subscriber
    subscriber = test_db.query(Subscriber).filter_by(email="alert@example.com").first()
    subscriber.confirmed = True
    test_db.commit()

    with patch("app.routers.subscribers.send_king_tide_alert", new_callable=AsyncMock) as mock_send:
        response = client.post(
            "/api/admin/test-alert",
            headers={"x-api-key": "test-key"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Test alert sent to 1 subscriber(s)"
    mock_send.assert_called_once()


def test_test_alert_no_confirmed_subscribers(client):
    """POST /api/admin/test-alert should return 404 if no confirmed subscribers."""
    response = client.post(
        "/api/admin/test-alert",
        headers={"x-api-key": "test-key"},
    )
    assert response.status_code == 404


def test_test_alert_rejected_without_api_key(client):
    """POST /api/admin/test-alert without API key should return 422."""
    response = client.post("/api/admin/test-alert")
    assert response.status_code == 422


def test_test_alert_rejected_with_wrong_api_key(client):
    """POST /api/admin/test-alert with wrong API key should return 403."""
    response = client.post(
        "/api/admin/test-alert",
        headers={"x-api-key": "wrong-key"},
    )
    assert response.status_code == 403
