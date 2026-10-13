import hashlib
import hmac
import json
import logging
import time
from unittest.mock import MagicMock, patch

from app.config import settings


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


def test_create_checkout_session_amount_below_minimum_rejected(client):
    response = client.post(
        "/api/stripe/create-checkout-session",
        json={"amount": 50},
    )
    assert response.status_code == 422


def test_create_checkout_session_amount_above_maximum_rejected(client):
    response = client.post(
        "/api/stripe/create-checkout-session",
        json={"amount": 10_000_000},
    )
    assert response.status_code == 422


def _signed(payload: str, secret: str) -> str:
    ts = int(time.time())
    digest = hmac.new(secret.encode(), f"{ts}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={digest}"


def test_webhook_handles_real_stripe_event_objects(client, caplog):
    """A genuinely signed event yields Stripe objects, not dicts; the handler must cope."""
    secret = "whsec_test_secret"
    original = settings.STRIPE_WEBHOOK_SECRET
    settings.STRIPE_WEBHOOK_SECRET = secret
    payload = json.dumps(
        {
            "id": "evt_1", "object": "event", "type": "checkout.session.completed",
            "api_version": "2025-01-27.acacia",
            "data": {"object": {"id": "cs_1", "object": "checkout.session", "amount_total": 500}},
        }
    )
    try:
        with caplog.at_level(logging.INFO, logger="app.routers.stripe"):
            response = client.post(
                "/api/stripe/webhook",
                content=payload,
                headers={"stripe-signature": _signed(payload, secret), "Content-Type": "application/json"},
            )
    finally:
        settings.STRIPE_WEBHOOK_SECRET = original

    assert response.status_code == 200
    assert "Payment received: 5.00 USD" in caplog.text


def test_webhook_never_fails_after_signature_check(client, caplog):
    """An unexpected payload shape is logged, not turned into a 500 (which makes Stripe retry)."""
    secret = "whsec_test_secret"
    original = settings.STRIPE_WEBHOOK_SECRET
    settings.STRIPE_WEBHOOK_SECRET = secret
    payload = json.dumps(
        {
            "id": "evt_2", "object": "event", "type": "checkout.session.completed",
            "api_version": "2025-01-27.acacia",
            "data": {"object": {"id": "cs_2", "object": "checkout.session"}},
        }
    )
    try:
        with caplog.at_level(logging.ERROR, logger="app.routers.stripe"):
            response = client.post(
                "/api/stripe/webhook",
                content=payload,
                headers={"stripe-signature": _signed(payload, secret), "Content-Type": "application/json"},
            )
    finally:
        settings.STRIPE_WEBHOOK_SECRET = original

    assert response.status_code == 200
    assert "handled but not recorded" in caplog.text
