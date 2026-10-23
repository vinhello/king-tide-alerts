"""Admin funnel: signups, confirmation, nudges, churn and delivery per run."""

from datetime import datetime, timedelta, timezone

from app.models.email_event import EmailEvent, EmailEventType
from app.models.notification_sent import NotificationSent, NotificationType
from app.models.subscriber import Subscriber
from app.services import funnel

ADMIN = {"x-admin-password": "test-password"}
NOW = datetime.now(timezone.utc)


def _sub(db, email, days_ago, confirmed=False, confirm_after_hours=None, utm=None, referrer=None, landing="/", unsubscribed_days_ago=None):
    created = NOW - timedelta(days=days_ago)
    row = Subscriber(
        name=email.split("@")[0],
        email=email,
        notification_preference="email",
        unsubscribe_token=f"token-{email}",
        confirmed=confirmed,
        created_at=created,
        confirmed_at=created + timedelta(hours=confirm_after_hours) if confirm_after_hours is not None else None,
        unsubscribed_at=NOW - timedelta(days=unsubscribed_days_ago) if unsubscribed_days_ago is not None else None,
        signup_utm_source=utm,
        signup_referrer=referrer,
        signup_landing_path=landing,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_source_label_prefers_utm_then_referrer_host_then_direct():
    assert funnel.source_label("Nextdoor", None, "/") == "nextdoor"
    assert funnel.source_label(None, "https://www.google.com/search?q=x", "/") == "google.com"
    assert funnel.source_label(None, None, "/") == funnel.DIRECT
    assert funnel.source_label(None, None, None) == funnel.NOT_RECORDED


def test_funnel_endpoint_computes_stages_sources_weeks_and_runs(client, test_db):
    # All time: 5 signups, 3 confirmed (one of them later unsubscribed), 1 nudged then confirmed.
    old = _sub(test_db, "old@example.com", days_ago=120, confirmed=True, landing=None)
    fast = _sub(test_db, "fast@example.com", days_ago=10, confirmed=True, confirm_after_hours=1, referrer="https://www.google.com/")
    slow = _sub(test_db, "slow@example.com", days_ago=8, confirmed=True, confirm_after_hours=50, utm="nextdoor")
    never = _sub(test_db, "never@example.com", days_ago=5)
    _sub(test_db, "gone@example.com", days_ago=40, confirmed=False, confirm_after_hours=2, unsubscribed_days_ago=3)
    # A nudge went to "slow" before they confirmed, and to "never" who did not.
    for sub, hours_after_signup in ((slow, 20), (never, 24)):
        test_db.add(
            NotificationSent(
                subscriber_id=sub.id,
                notification_type=NotificationType.CONFIRMATION,
                sent_at=sub.created_at + timedelta(hours=hours_after_signup),
            )
        )
    # One alert run three days ago: two sends, one delivered, one without an outcome.
    run_day = NOW - timedelta(days=3)
    delivered = NotificationSent(subscriber_id=fast.id, notification_type=NotificationType.SEVEN_DAY_ALERT, sent_at=run_day, provider_message_id="re_1")
    silent = NotificationSent(subscriber_id=old.id, notification_type=NotificationType.SEVEN_DAY_ALERT, sent_at=run_day, provider_message_id="re_2")
    test_db.add_all([delivered, silent])
    test_db.commit()
    test_db.add(EmailEvent(svix_id="msg_1", provider_message_id="re_1", notification_id=delivered.id, event_type=EmailEventType.DELIVERED, occurred_at=run_day))
    test_db.commit()

    response = client.get("/api/admin/funnel", headers=ADMIN)

    assert response.status_code == 200
    data = response.json()

    all_time = data["all_time"]
    assert all_time["signups"] == 5
    assert all_time["confirmed"] == 4  # old, fast, slow, and gone (confirmed before unsubscribing)
    assert all_time["confirmation_rate"] == 0.8
    assert all_time["median_hours_to_confirm"] == 2.0  # hours known for fast (1), gone (2), slow (50)
    assert all_time["unsubscribed"] == 1
    assert all_time["nudged"] == 2
    assert all_time["confirmed_after_nudge"] == 1

    recent = data["last_30_days"]
    assert recent["signups"] == 3
    assert recent["confirmed"] == 2
    assert recent["unsubscribed"] == 1  # churn counts by when it happened

    sources = {s["source"]: s for s in data["by_source"]}
    assert sources["google.com"]["signups"] == 1
    assert sources["nextdoor"]["confirmed"] == 1
    assert sources[funnel.DIRECT]["signups"] == 2
    assert sources[funnel.NOT_RECORDED]["signups"] == 1

    assert len(data["weekly"]) == 12
    assert sum(w["signups"] for w in data["weekly"]) == 4  # the 120-day-old signup is outside the window
    assert sum(w["unsubscribed"] for w in data["weekly"]) == 1

    assert data["runs"] == [
        {
            "date": run_day.date().isoformat(),
            "notification_type": "seven_day_alert",
            "sent": 2,
            "delivered": 1,
            "bounced": 0,
            "complained": 0,
            "no_outcome": 1,
        }
    ]


def test_funnel_requires_auth(client):
    assert client.get("/api/admin/funnel").status_code == 401


def test_funnel_on_empty_database(client):
    data = client.get("/api/admin/funnel", headers=ADMIN).json()
    assert data["all_time"]["signups"] == 0
    assert data["all_time"]["confirmation_rate"] == 0.0
    assert data["all_time"]["median_hours_to_confirm"] is None
    assert data["by_source"] == []
    assert len(data["weekly"]) == 12
    assert data["runs"] == []
