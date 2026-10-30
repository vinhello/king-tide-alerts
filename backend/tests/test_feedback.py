import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.config import settings
from app.rate_limit import limiter
from app.services.feedback_stats import feedback_stats
from app.services.notification import EmailSendError, send_feedback
from app.utils.email_templates import feedback_email


@pytest.fixture(autouse=True)
def reset_rate_limits():
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(autouse=True)
def reset_feedback_stats():
    feedback_stats.reset()
    yield
    feedback_stats.reset()


def test_feedback_sends_email(client):
    with patch(
        "app.routers.feedback.send_feedback", new_callable=AsyncMock
    ) as mock_send:
        response = client.post(
            "/api/feedback",
            json={
                "message": "The path flooded at 8am near Bothin Marsh.",
                "subject": "Flooding report",
                "email": "rider@example.com",
            },
        )

    assert response.status_code == 200
    assert "sent" in response.json()["message"].lower()
    mock_send.assert_called_once_with(
        message="The path flooded at 8am near Bothin Marsh.",
        subject="Flooding report",
        reply_email="rider@example.com",
    )


def test_feedback_optional_fields_blank_become_none(client):
    with patch(
        "app.routers.feedback.send_feedback", new_callable=AsyncMock
    ) as mock_send:
        response = client.post(
            "/api/feedback",
            json={"message": "  Just saying thanks  ", "subject": "", "email": ""},
        )

    assert response.status_code == 200
    mock_send.assert_called_once_with(
        message="Just saying thanks", subject=None, reply_email=None
    )


def test_feedback_message_required(client):
    response = client.post("/api/feedback", json={"subject": "No message"})
    assert response.status_code == 422


def test_feedback_blank_message_rejected(client):
    response = client.post("/api/feedback", json={"message": "   "})
    assert response.status_code == 422


def test_feedback_message_too_long_rejected(client):
    too_long = "x" * (settings.FEEDBACK_MAX_MESSAGE_LENGTH + 1)
    response = client.post("/api/feedback", json={"message": too_long})
    assert response.status_code == 422


def test_feedback_invalid_email_rejected(client):
    response = client.post(
        "/api/feedback", json={"message": "hello", "email": "not-an-email"}
    )
    assert response.status_code == 422


def test_feedback_honeypot_is_silently_dropped(client):
    with patch(
        "app.routers.feedback.send_feedback", new_callable=AsyncMock
    ) as mock_send:
        response = client.post(
            "/api/feedback",
            json={"message": "buy my product", "website": "http://spam.example"},
        )

    # Looks like success to the bot, but nothing is sent.
    assert response.status_code == 200
    mock_send.assert_not_called()


def test_feedback_send_failure_is_reported_to_visitor(client):
    with patch(
        "app.routers.feedback.send_feedback",
        new_callable=AsyncMock,
        side_effect=EmailSendError("Resend: 500 Internal Server Error"),
    ):
        response = client.post("/api/feedback", json={"message": "hello"})

    assert response.status_code == 503
    assert "try again" in response.json()["detail"].lower()
    assert feedback_stats.failed == 1
    assert feedback_stats.sent == 0
    assert "500" in feedback_stats.last_failure_reason
    assert feedback_stats.last_failure_at is not None


def test_feedback_counts_outcomes(client):
    with patch("app.routers.feedback.send_feedback", new_callable=AsyncMock):
        client.post("/api/feedback", json={"message": "hello"})
        client.post(
            "/api/feedback", json={"message": "spam", "website": "http://x.example"}
        )

    assert feedback_stats.sent == 1
    assert feedback_stats.bot_dropped == 1
    assert feedback_stats.failed == 0


def test_feedback_rate_limited_per_client(client):
    with patch("app.routers.feedback.send_feedback", new_callable=AsyncMock):
        for _ in range(3):
            ok = client.post("/api/feedback", json={"message": "hello"})
            assert ok.status_code == 200
        limited = client.post("/api/feedback", json={"message": "hello"})

    assert limited.status_code == 429


def test_feedback_email_template_escapes_html():
    html = feedback_email(
        subject="<b>Subject</b>",
        message="<script>alert(1)</script>\nsecond line",
        reply_email="rider@example.com",
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;Subject&lt;/b&gt;" in html
    assert "<br>" in html
    assert "rider@example.com" in html


def test_send_feedback_sets_reply_to_and_destination():
    with patch("app.services.notification.resend.Emails.send") as mock_resend:
        asyncio.run(
            send_feedback(
                message="Great service", subject=None, reply_email="rider@example.com"
            )
        )

    params = mock_resend.call_args.args[0]
    assert params["to"] == [settings.FEEDBACK_EMAIL]
    assert params["reply_to"] == "rider@example.com"
    assert "feedback" in params["subject"].lower()


def test_send_feedback_raises_when_resend_fails():
    with patch(
        "app.services.notification.resend.Emails.send",
        side_effect=RuntimeError("connection reset"),
    ):
        with pytest.raises(EmailSendError, match="connection reset"):
            asyncio.run(send_feedback(message="x", subject=None, reply_email=None))


def test_send_feedback_accepted_when_notifications_disabled():
    with (
        patch.object(settings, "NOTIFICATIONS_ENABLED", False),
        patch("app.services.notification.resend.Emails.send") as mock_resend,
    ):
        asyncio.run(send_feedback(message="x", subject=None, reply_email=None))

    mock_resend.assert_not_called()


def test_send_feedback_without_email_omits_reply_to():
    with patch("app.services.notification.resend.Emails.send") as mock_resend:
        asyncio.run(send_feedback(message="Great service", subject="Hi", reply_email=None))

    params = mock_resend.call_args.args[0]
    assert "reply_to" not in params
    assert "Hi" in params["subject"]
