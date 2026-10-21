"""List-Unsubscribe headers and the one-click POST endpoint."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from app.config import settings
from app.models.subscriber import NotificationPreference, Subscriber
from app.services.notification import send_email, send_king_tide_alert, unsubscribe_headers


def _with_api_url(value: str):
    class _Ctx:
        def __enter__(self):
            self.original = settings.PUBLIC_API_URL
            settings.PUBLIC_API_URL = value

        def __exit__(self, *exc):
            settings.PUBLIC_API_URL = self.original

    return _Ctx()


def test_headers_point_at_api_with_one_click_when_public_url_set():
    with _with_api_url("https://api.example.com/"):
        headers = unsubscribe_headers("tok123")
    assert headers["List-Unsubscribe"] == "<https://api.example.com/api/unsubscribe/tok123>"
    assert headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"


def test_headers_fall_back_to_site_page_without_one_click():
    with _with_api_url(""):
        headers = unsubscribe_headers("tok123")
    assert headers == {"List-Unsubscribe": f"<{settings.APP_URL}/unsubscribe/tok123>"}


def test_send_email_passes_headers_to_resend():
    with patch("app.services.notification.resend.Emails.send") as mock_resend:
        asyncio.run(send_email("a@example.com", "s", "<p>x</p>", headers={"X-Test": "1"}))
    assert mock_resend.call_args.args[0]["headers"] == {"X-Test": "1"}


def test_send_email_omits_headers_key_when_none():
    with patch("app.services.notification.resend.Emails.send") as mock_resend:
        asyncio.run(send_email("a@example.com", "s", "<p>x</p>"))
    assert "headers" not in mock_resend.call_args.args[0]


def test_alert_email_carries_unsubscribe_headers():
    subscriber = Subscriber(
        name="Rider", email="rider@example.com",
        notification_preference=NotificationPreference.EMAIL,
        unsubscribe_token="tok-rider", confirmed=True,
    )
    when = datetime.now(timezone.utc) + timedelta(days=7)
    with _with_api_url("https://api.example.com"), patch(
        "app.services.notification.send_email", new_callable=AsyncMock
    ) as mock_send:
        asyncio.run(
            send_king_tide_alert(
                subscriber=subscriber, period_start=when, period_end=when,
                peak_datetime=when, peak_height=6.8, days_until=7,
            )
        )
    headers = mock_send.call_args.kwargs["headers"]
    assert headers["List-Unsubscribe"] == "<https://api.example.com/api/unsubscribe/tok-rider>"
    assert headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"


def test_one_click_post_unsubscribes_idempotently(client, test_db):
    test_db.add(
        Subscriber(
            name="Rider", email="rider@example.com",
            notification_preference=NotificationPreference.EMAIL,
            unsubscribe_token="tok-post", confirmed=True,
        )
    )
    test_db.commit()

    first = client.post(
        "/api/unsubscribe/tok-post",
        content="List-Unsubscribe=One-Click",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert first.status_code == 200
    sub = test_db.query(Subscriber).filter(Subscriber.unsubscribe_token == "tok-post").first()
    test_db.refresh(sub)
    assert sub.unsubscribed_at is not None
    stamp = sub.unsubscribed_at

    second = client.post("/api/unsubscribe/tok-post")
    assert second.status_code == 200
    test_db.refresh(sub)
    assert sub.unsubscribed_at == stamp


def test_one_click_post_rejects_unknown_token(client):
    assert client.post("/api/unsubscribe/nope").status_code == 404


def test_subject_says_one_day_away_without_a_plural():
    from datetime import datetime, timezone

    from app.services.notification import build_king_tide_alert_email

    when = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
    one, _ = build_king_tide_alert_email("A", when, when, when, 6.2, 1, "u")
    two, _ = build_king_tide_alert_email("A", when, when, when, 6.2, 2, "u")
    seven, _ = build_king_tide_alert_email("A", when, when, when, 6.2, 7, "u")
    assert one.endswith("1 day away")
    assert two.endswith("2 days away")
    assert seven.endswith("7 days away")
