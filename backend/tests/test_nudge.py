from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.notification_sent import NotificationSent, NotificationType
from app.models.subscriber import NotificationPreference, Subscriber
from app.rate_limit import limiter
from app.services.nudge import find_unconfirmed, nudge_unconfirmed
from app.utils.email_templates import confirmation_reminder_email

HEADERS = {"x-admin-password": "test-password"}


@pytest.fixture(autouse=True)
def reset_rate_limits():
    limiter.reset()
    yield
    limiter.reset()


def _signup(db, email, *, confirmed=False, days_ago=2, name="Rider"):
    sub = Subscriber(
        name=name, email=email, notification_preference=NotificationPreference.EMAIL,
        unsubscribe_token=f"tok-{email}", confirmed=confirmed,
        created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def test_find_unconfirmed_filters_confirmed_old_and_already_nudged(test_db):
    recent = _signup(test_db, "recent@example.com", days_ago=2)
    _signup(test_db, "confirmed@example.com", confirmed=True)
    _signup(test_db, "old@example.com", days_ago=45)
    nudged = _signup(test_db, "nudged@example.com", days_ago=3)
    test_db.add(NotificationSent(subscriber_id=nudged.id, notification_type=NotificationType.CONFIRMATION))
    test_db.commit()

    found = find_unconfirmed(test_db, window_days=30)
    assert [s.id for s in found] == [recent.id]


def test_find_unconfirmed_skips_signups_younger_than_min_age(test_db):
    fresh = _signup(test_db, "fresh@example.com", days_ago=0.1)
    ready = _signup(test_db, "ready@example.com", days_ago=1.5)

    found = find_unconfirmed(test_db, window_days=30)
    assert [s.id for s in found] == [ready.id]

    everyone = find_unconfirmed(test_db, window_days=30, min_age_hours=0)
    assert {s.id for s in everyone} == {fresh.id, ready.id}


@pytest.mark.asyncio
async def test_nudge_dry_run_lists_and_sends_nothing(test_db):
    _signup(test_db, "a@example.com", name="A")
    _signup(test_db, "b@example.com", name="B")

    with patch(
        "app.services.notification.send_confirmation_reminder", new_callable=AsyncMock, return_value="re_test"
    ) as send:
        outcome = await nudge_unconfirmed(test_db, window_days=30, dry_run=True)

    assert outcome.dry_run is True
    assert sorted(r.email for r in outcome.recipients) == ["a@example.com", "b@example.com"]
    assert outcome.sent == 0
    send.assert_not_called()
    assert test_db.query(NotificationSent).count() == 0


@pytest.mark.asyncio
async def test_nudge_real_run_sends_records_and_dedupes(test_db):
    _signup(test_db, "a@example.com")
    _signup(test_db, "b@example.com")

    with patch(
        "app.services.notification.send_confirmation_reminder", new_callable=AsyncMock, return_value="re_test"
    ) as send:
        first = await nudge_unconfirmed(test_db, window_days=30, dry_run=False)
        second = await nudge_unconfirmed(test_db, window_days=30, dry_run=False)

    assert first.sent == 2
    assert send.await_count == 2
    reminders = test_db.query(NotificationSent).filter(
        NotificationSent.notification_type == NotificationType.CONFIRMATION
    ).all()
    assert len(reminders) == 2
    assert all(r.provider_message_id == "re_test" for r in reminders)
    # Nobody is reminded twice.
    assert second.recipients == [] and second.sent == 0


def test_admin_nudge_defaults_to_dry_run(client, test_db):
    _signup(test_db, "a@example.com", name="Alice")

    with patch(
        "app.services.notification.send_confirmation_reminder", new_callable=AsyncMock, return_value="re_test"
    ) as send:
        response = client.post("/api/admin/nudge-unconfirmed", headers=HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["dry_run"] is True
    assert data["recipient_count"] == 1
    assert data["recipients"][0]["email"] == "a@example.com"
    assert data["sent"] == 0
    assert "Confirm Subscription" in data["sample_email_html"]
    send.assert_not_called()


def test_admin_nudge_sends_only_when_explicitly_asked(client, test_db):
    _signup(test_db, "a@example.com")

    with patch(
        "app.services.notification.send_confirmation_reminder", new_callable=AsyncMock, return_value="re_test"
    ) as send:
        response = client.post("/api/admin/nudge-unconfirmed?dry_run=false", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["sent"] == 1
    send.assert_awaited_once()


def test_admin_nudge_min_age_defaults_to_a_day(client, test_db):
    _signup(test_db, "fresh@example.com", days_ago=0.1)

    default = client.post("/api/admin/nudge-unconfirmed", headers=HEADERS)
    assert default.status_code == 200
    assert default.json()["min_age_hours"] == 24
    assert default.json()["recipient_count"] == 0

    disabled = client.post(
        "/api/admin/nudge-unconfirmed?min_age_hours=0", headers=HEADERS
    )
    assert disabled.status_code == 200
    assert disabled.json()["recipient_count"] == 1


def test_admin_nudge_requires_auth(client):
    response = client.post("/api/admin/nudge-unconfirmed")
    assert response.status_code == 401


def test_reminder_template_escapes_and_links():
    html = confirmation_reminder_email("<b>Vince</b>", "https://x/confirm/t", "October 3, 2026")
    assert "&lt;b&gt;Vince&lt;/b&gt;" in html
    assert "https://x/confirm/t" in html
    assert "October 3, 2026" in html
    assert "King Tide Alert is free" in html
    assert "a heads-up 7 days ahead and a reminder 48 hours ahead" in html
    assert "and nothing else" not in html


def test_confirmation_email_says_free():
    from app.utils.email_templates import confirmation_email

    html = confirmation_email("Vince", "https://x/confirm/t")
    assert "It's free, and you can unsubscribe any time" in html
    assert "King Tide Alerts for the SF Bay Area" not in html



def test_find_unconfirmed_excludes_unsubscribed(test_db):
    kept = _signup(test_db, "kept@example.com")
    gone = _signup(test_db, "gone@example.com")
    gone.unsubscribed_at = datetime.now(timezone.utc)
    test_db.commit()

    found = find_unconfirmed(test_db, window_days=30)
    assert [s.id for s in found] == [kept.id]
