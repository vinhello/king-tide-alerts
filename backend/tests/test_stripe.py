from unittest.mock import MagicMock, patch


def test_create_checkout_session(client):
    """POST /api/stripe/create-checkout-session should return a checkout URL."""
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/test_session_123"

    with patch("app.routers.stripe.stripe.checkout.Session.create", return_value=mock_session):
        response = client.post(
            "/api/stripe/create-checkout-session",
            json={"amount": 500},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["checkout_url"] == "https://checkout.stripe.com/test_session_123"


def test_webhook_valid_signature(client):
    """Valid Stripe webhook should return 200."""
    mock_event = {
        "type": "checkout.session.completed",
        "data": {"object": {"amount_total": 500}},
    }

    with patch(
        "app.routers.stripe.stripe.Webhook.construct_event",
        return_value=mock_event,
    ):
        response = client.post(
            "/api/stripe/webhook",
            content=b'{"test": "payload"}',
            headers={"stripe-signature": "test_sig"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_webhook_invalid_signature_rejected(client):
    """Invalid Stripe webhook signature should return 400."""
    import stripe

    with patch(
        "app.routers.stripe.stripe.Webhook.construct_event",
        side_effect=stripe.SignatureVerificationError("Invalid", "sig"),
    ):
        response = client.post(
            "/api/stripe/webhook",
            content=b'{"test": "payload"}',
            headers={"stripe-signature": "bad_sig"},
        )

    assert response.status_code == 400
