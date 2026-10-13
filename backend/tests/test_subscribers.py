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


def test_subscribe_duplicate_confirmed_email_rejected(client, test_db):
    """A confirmed address cannot subscribe again."""
    from app.models.subscriber import Subscriber

    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock) as mock_send:
        client.post(
            "/api/subscribe",
            json={"name": "Test", "email": "dup@example.com", "notification_preference": "email"},
        )
        test_db.query(Subscriber).filter(Subscriber.email == "dup@example.com").update(
            {Subscriber.confirmed: True}
        )
        test_db.commit()
        mock_send.reset_mock()

        response = client.post(
            "/api/subscribe",
            json={"name": "Test", "email": "dup@example.com", "notification_preference": "email"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already subscribed"
    mock_send.assert_not_called()


def test_subscribe_unconfirmed_duplicate_resends_confirmation(client, test_db):
    """Signing up again before confirming resends the email instead of failing."""
    from app.models.subscriber import Subscriber

    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock) as mock_send:
        first = client.post(
            "/api/subscribe",
            json={"name": "Test", "email": "again@example.com", "notification_preference": "email"},
        )
        second = client.post(
            "/api/subscribe",
            json={"name": "Test", "email": "again@example.com", "notification_preference": "email"},
        )

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]
    assert mock_send.call_count == 2
    assert test_db.query(Subscriber).filter(Subscriber.email == "again@example.com").count() == 1


def test_resend_confirmation_sends_for_unconfirmed(client, test_db):
    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock) as mock_send:
        client.post(
            "/api/subscribe",
            json={"name": "Test", "email": "lost@example.com", "notification_preference": "email"},
        )
        mock_send.reset_mock()
        response = client.post("/api/resend-confirmation", json={"email": "lost@example.com"})

    assert response.status_code == 200
    assert "on its way" in response.json()["message"]
    mock_send.assert_called_once()
    assert mock_send.call_args.args[0].email == "lost@example.com"


def test_resend_confirmation_silent_for_confirmed_and_unknown(client, test_db):
    """Same response, no email, whether the address is confirmed or unknown."""
    from app.models.subscriber import Subscriber

    test_db.add(
        Subscriber(
            name="Done", email="done@example.com", notification_preference="email",
            unsubscribe_token="tok-done", confirmed=True,
        )
    )
    test_db.commit()

    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock) as mock_send:
        confirmed = client.post("/api/resend-confirmation", json={"email": "done@example.com"})
        unknown = client.post("/api/resend-confirmation", json={"email": "nobody@example.com"})

    assert confirmed.status_code == 200 and unknown.status_code == 200
    assert confirmed.json() == unknown.json()
    mock_send.assert_not_called()


def test_resend_confirmation_rejects_invalid_email(client):
    response = client.post("/api/resend-confirmation", json={"email": "not-an-email"})
    assert response.status_code == 422


def test_resend_confirmation_rate_limited(client):
    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        for _ in range(3):
            assert client.post("/api/resend-confirmation", json={"email": "x@example.com"}).status_code == 200
        limited = client.post("/api/resend-confirmation", json={"email": "x@example.com"})
    assert limited.status_code == 429


def test_subscribe_rate_limited(client):
    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        for i in range(5):
            r = client.post(
                "/api/subscribe",
                json={"name": "T", "email": f"rl{i}@example.com", "notification_preference": "email"},
            )
            assert r.status_code == 201
        limited = client.post(
            "/api/subscribe",
            json={"name": "T", "email": "rl9@example.com", "notification_preference": "email"},
        )
    assert limited.status_code == 429


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


def test_unsubscribe_erases_personal_data_and_is_idempotent(client, test_db):
    """Unsubscribing deletes name, email and phone, keeps an anonymous record, and repeats safely."""
    from app.models.subscriber import Subscriber

    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        client.post(
            "/api/subscribe",
            json={
                "name": "Test", "email": "bye@example.com", "notification_preference": "email",
                "signup_utm_source": "nextdoor",
            },
        )
    sub = test_db.query(Subscriber).filter(Subscriber.email == "bye@example.com").first()
    token = sub.unsubscribe_token

    first = client.get(f"/api/unsubscribe/{token}")
    assert first.status_code == 200
    test_db.refresh(sub)
    assert sub.unsubscribed_at is not None
    assert sub.email is None and sub.phone is None and sub.name == ""
    assert sub.confirmed is False
    # Anonymous record survives for counting
    assert sub.signup_utm_source == "nextdoor"
    assert sub.created_at is not None
    stamp = sub.unsubscribed_at

    second = client.get(f"/api/unsubscribe/{token}")
    assert second.status_code == 200
    test_db.refresh(sub)
    assert sub.unsubscribed_at == stamp
    assert test_db.query(Subscriber).count() == 1


def test_unsubscribe_invalid_token(client):
    assert client.get("/api/unsubscribe/nope").status_code == 404


def test_subscribe_stores_signup_source(client, test_db):
    from app.models.subscriber import Subscriber

    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        response = client.post(
            "/api/subscribe",
            json={
                "name": "Test", "email": "src@example.com", "notification_preference": "email",
                "signup_referrer": "https://nextdoor.com/p/abc",
                "signup_utm_source": "nextdoor", "signup_utm_medium": "social",
                "signup_utm_campaign": "oct-flood", "signup_landing_path": "/",
            },
        )
    assert response.status_code == 201
    sub = test_db.query(Subscriber).filter(Subscriber.email == "src@example.com").first()
    assert sub.signup_referrer == "https://nextdoor.com/p/abc"
    assert sub.signup_utm_source == "nextdoor"
    assert sub.signup_utm_medium == "social"
    assert sub.signup_utm_campaign == "oct-flood"
    assert sub.signup_landing_path == "/"


def test_subscribe_source_is_optional(client, test_db):
    from app.models.subscriber import Subscriber

    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        response = client.post(
            "/api/subscribe",
            json={"name": "Test", "email": "nosrc@example.com", "notification_preference": "email"},
        )
    assert response.status_code == 201
    sub = test_db.query(Subscriber).filter(Subscriber.email == "nosrc@example.com").first()
    assert sub.signup_referrer is None and sub.signup_utm_source is None


def test_confirm_sets_confirmed_at_once(client, test_db):
    from app.models.subscriber import Subscriber

    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        client.post(
            "/api/subscribe",
            json={"name": "Test", "email": "when@example.com", "notification_preference": "email"},
        )
    sub = test_db.query(Subscriber).filter(Subscriber.email == "when@example.com").first()
    assert sub.confirmed_at is None

    assert client.get(f"/api/confirm/{sub.unsubscribe_token}").status_code == 200
    test_db.refresh(sub)
    assert sub.confirmed is True and sub.confirmed_at is not None
    first_stamp = sub.confirmed_at

    assert client.get(f"/api/confirm/{sub.unsubscribe_token}").status_code == 200
    test_db.refresh(sub)
    assert sub.confirmed_at == first_stamp


def test_confirm_after_unsubscribe_is_refused(client, test_db):
    from app.models.subscriber import Subscriber

    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock):
        client.post(
            "/api/subscribe",
            json={"name": "Test", "email": "gone@example.com", "notification_preference": "email"},
        )
    sub = test_db.query(Subscriber).filter(Subscriber.email == "gone@example.com").first()
    client.get(f"/api/unsubscribe/{sub.unsubscribe_token}")

    response = client.get(f"/api/confirm/{sub.unsubscribe_token}")
    assert response.status_code == 410
    test_db.refresh(sub)
    assert sub.confirmed is False and sub.unsubscribed_at is not None


def test_resubscribe_after_unsubscribe_creates_fresh_record(client, test_db):
    """After unsubscribing, signing up again starts over: a new row, the old one stays anonymous."""
    from app.models.subscriber import Subscriber

    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock) as mock_send:
        client.post(
            "/api/subscribe",
            json={"name": "Old Name", "email": "back@example.com", "notification_preference": "email"},
        )
        old = test_db.query(Subscriber).filter(Subscriber.email == "back@example.com").first()
        old_id = old.id
        client.get(f"/api/confirm/{old.unsubscribe_token}")
        client.get(f"/api/unsubscribe/{old.unsubscribe_token}")
        mock_send.reset_mock()

        response = client.post(
            "/api/subscribe",
            json={"name": "New Name", "email": "back@example.com", "notification_preference": "email"},
        )

    assert response.status_code == 201
    assert response.json()["id"] != str(old_id)
    assert test_db.query(Subscriber).count() == 2
    fresh = test_db.query(Subscriber).filter(Subscriber.email == "back@example.com").one()
    assert fresh.confirmed is False and fresh.unsubscribed_at is None
    old = test_db.get(Subscriber, old_id)
    assert old.email is None and old.unsubscribed_at is not None
    mock_send.assert_called_once()


def test_resend_confirmation_skips_unsubscribed(client, test_db):
    from app.models.subscriber import Subscriber

    with patch("app.routers.subscribers.send_confirmation", new_callable=AsyncMock) as mock_send:
        client.post(
            "/api/subscribe",
            json={"name": "Test", "email": "left@example.com", "notification_preference": "email"},
        )
        sub = test_db.query(Subscriber).filter(Subscriber.email == "left@example.com").first()
        client.get(f"/api/unsubscribe/{sub.unsubscribe_token}")
        mock_send.reset_mock()
        response = client.post("/api/resend-confirmation", json={"email": "left@example.com"})

    assert response.status_code == 200
    mock_send.assert_not_called()


def test_invalid_token_returns_404(client):
    """Confirm/unsubscribe with bad token should return 404."""
    response = client.get("/api/confirm/invalid-token-xyz")
    assert response.status_code == 404

    response = client.get("/api/unsubscribe/invalid-token-xyz")
    assert response.status_code == 404
