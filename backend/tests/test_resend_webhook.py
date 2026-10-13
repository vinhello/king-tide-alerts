"""POST /api/webhooks/resend: delivery outcomes and the suppression rule.

Signatures follow the Svix scheme Resend uses: HMAC-SHA256 over
"{svix-id}.{svix-timestamp}.{body}" keyed with the base64 secret after
"whsec_". No test here sends email; the send path is asserted untouched.
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.config import settings
from app.models.email_event import EmailEvent, EmailEventType
from app.models.notification_sent import NotificationSent, NotificationType
from app.models.subscriber import Subscriber

SECRET = "whsec_" + base64.b64encode(b"test-signing-secret-for-webhooks").decode()
ADMIN = {"x-admin-password": "test-password"}

PERMANENT = {"type": "Permanent", "subType": "General", "message": "550 5.1.1 user unknown"}
TEMPORARY = {"type": "Temporary", "subType": "MailboxFull", "message": "452 4.2.2 mailbox full"}


@pytest.fixture(autouse=True)
def webhook_secret():
    original = settings.RESEND_WEBHOOK_SECRET
    settings.RESEND_WEBHOOK_SECRET = SECRET
    yield
    settings.RESEND_WEBHOOK_SECRET = original


def _signed_headers(
    payload: str,
    svix_id: str = "msg_test_1",
    timestamp: int | None = None,
    secret: str = SECRET,
) -> dict[str, str]:
    ts = str(timestamp if timestamp is not None else int(time.time()))
    key = base64.b64decode(secret.split("_", 1)[1])
    digest = hmac.new(key, f"{svix_id}.{ts}.{payload}".encode(), hashlib.sha256).digest()
    return {
        "svix-id": svix_id,
        "svix-timestamp": ts,
        "svix-signature": "v1," + base64.b64encode(digest).decode(),
    }


def _event(
    event_type: str,
    email_id: str,
    to: str = "rider@example.com",
    bounce: dict | None = None,
) -> str:
    data = {
        "created_at": "2026-10-13T18:00:00.000Z",
        "email_id": email_id,
        "message_id": "<abc@alert.kingtidealert.com>",
        "from": "King Tide Alerts <alert@alert.kingtidealert.com>",
        "to": [to],
        "subject": "High Tide Alert",
    }
    if bounce is not None:
        data["bounce"] = bounce
    return json.dumps(
        {"type": event_type, "created_at": "2026-10-13T18:00:01.000Z", "data": data}
    )


def _post(client, payload: str, **signing):
    return client.post(
        "/api/webhooks/resend",
        content=payload,
        headers={"Content-Type": "application/json", **_signed_headers(payload, **signing)},
    )


def _subscriber_with_send(db, email="rider@example.com", message_id="re_abc"):
    subscriber = Subscriber(
        name="Rider",
        email=email,
        notification_preference="email",
        unsubscribe_token=f"token-{email}",
        confirmed=True,
        confirmed_at=datetime.now(timezone.utc),
    )
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    sent = NotificationSent(
        subscriber_id=subscriber.id,
        notification_type=NotificationType.SEVEN_DAY_ALERT,
        provider_message_id=message_id,
    )
    db.add(sent)
    db.commit()
    db.refresh(sent)
    return subscriber, sent


# --- verification -----------------------------------------------------------


def test_unconfigured_endpoint_answers_503(client):
    settings.RESEND_WEBHOOK_SECRET = ""
    response = _post(client, _event("email.delivered", "re_abc"))
    assert response.status_code == 503


def test_wrong_secret_is_rejected(client, test_db):
    _subscriber_with_send(test_db)
    other = "whsec_" + base64.b64encode(b"a-different-secret-entirely-xx").decode()
    response = _post(client, _event("email.delivered", "re_abc"), secret=other)
    assert response.status_code == 400
    assert test_db.query(EmailEvent).count() == 0


def test_tampered_body_is_rejected(client, test_db):
    _subscriber_with_send(test_db)
    payload = _event("email.delivered", "re_abc")
    headers = _signed_headers(payload)
    tampered = payload.replace("re_abc", "re_xyz")
    response = client.post(
        "/api/webhooks/resend",
        content=tampered,
        headers={"Content-Type": "application/json", **headers},
    )
    assert response.status_code == 400


def test_missing_signature_headers_are_rejected(client):
    response = client.post(
        "/api/webhooks/resend",
        content=_event("email.delivered", "re_abc"),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_stale_timestamp_is_rejected(client):
    payload = _event("email.delivered", "re_abc")
    response = _post(client, payload, timestamp=int(time.time()) - 3600)
    assert response.status_code == 400


# --- recording --------------------------------------------------------------


def test_delivered_event_is_linked_to_the_send(client, test_db):
    subscriber, sent = _subscriber_with_send(test_db)

    response = _post(client, _event("email.delivered", "re_abc"))

    assert response.status_code == 200
    assert response.json()["result"] == "recorded"
    event = test_db.query(EmailEvent).one()
    assert event.event_type == EmailEventType.DELIVERED
    assert event.notification_id == sent.id
    assert event.subscriber_id == subscriber.id
    assert event.svix_id == "msg_test_1"
    assert event.occurred_at.year == 2026
    test_db.refresh(subscriber)
    assert subscriber.confirmed is True
    assert subscriber.unsubscribed_at is None

    stats = client.get("/api/admin/notifications", headers=ADMIN).json()
    assert stats["delivered"] == 1
    assert stats["bounced"] == 0
    assert stats["complained"] == 0
    assert stats["recent"][0]["delivery_status"] == "delivered"


def test_retry_with_same_svix_id_is_recorded_once(client, test_db):
    _subscriber_with_send(test_db)
    payload = _event("email.delivered", "re_abc")

    first = _post(client, payload)
    second = _post(client, payload)

    assert first.json()["result"] == "recorded"
    assert second.json()["result"] == "duplicate"
    assert test_db.query(EmailEvent).count() == 1


def test_unhandled_event_types_are_acknowledged_and_dropped(client, test_db):
    _subscriber_with_send(test_db)
    response = _post(client, _event("email.opened", "re_abc"))
    assert response.status_code == 200
    assert response.json()["result"] == "ignored"
    assert test_db.query(EmailEvent).count() == 0


def test_unknown_message_and_address_is_still_recorded(client, test_db):
    response = _post(client, _event("email.delivered", "re_nobody", to="nobody@example.com"))
    assert response.json()["result"] == "recorded"
    event = test_db.query(EmailEvent).one()
    assert event.notification_id is None
    assert event.subscriber_id is None


def test_sends_without_an_outcome_show_as_sent_or_unknown(client, test_db):
    subscriber, _ = _subscriber_with_send(test_db, message_id="re_pending")
    older = NotificationSent(
        subscriber_id=subscriber.id,
        notification_type=NotificationType.FORTY_EIGHT_HOUR_REMINDER,
        provider_message_id=None,
        sent_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    test_db.add(older)
    test_db.commit()

    recent = client.get("/api/admin/notifications", headers=ADMIN).json()["recent"]
    assert [r["delivery_status"] for r in recent] == ["sent", "unknown"]


# --- suppression ------------------------------------------------------------


def test_permanent_bounce_stops_sending_and_erases_personal_data(client, test_db):
    subscriber, _ = _subscriber_with_send(test_db)

    with patch("app.services.notification.resend.Emails.send") as mock_send:
        response = _post(client, _event("email.bounced", "re_abc", bounce=PERMANENT))

    assert response.status_code == 200
    assert response.json()["result"] == "suppressed"
    mock_send.assert_not_called()

    test_db.refresh(subscriber)
    assert subscriber.unsubscribed_at is not None
    assert subscriber.confirmed is False
    assert subscriber.name == ""
    assert subscriber.email is None
    assert subscriber.phone is None
    assert subscriber.unsubscribe_token == "token-rider@example.com"

    event = test_db.query(EmailEvent).one()
    assert event.bounce_type == "Permanent"
    assert event.detail == "General: 550 5.1.1 user unknown"

    stats = client.get("/api/admin/notifications", headers=ADMIN).json()
    assert stats["bounced"] == 1
    assert stats["recent"][0]["delivery_status"] == "bounced"
    assert client.get("/api/admin/stats", headers=ADMIN).json()["unsubscribed"] == 1


def test_second_hard_bounce_for_a_gone_subscriber_is_just_recorded(client, test_db):
    _subscriber_with_send(test_db)
    _post(client, _event("email.bounced", "re_abc", bounce=PERMANENT), svix_id="msg_1")

    response = _post(
        client, _event("email.bounced", "re_abc", bounce=PERMANENT), svix_id="msg_2"
    )

    assert response.json()["result"] == "recorded"
    assert test_db.query(EmailEvent).count() == 2


def test_temporary_bounce_is_recorded_without_suppressing(client, test_db):
    subscriber, _ = _subscriber_with_send(test_db)

    response = _post(client, _event("email.bounced", "re_abc", bounce=TEMPORARY))

    assert response.json()["result"] == "recorded"
    test_db.refresh(subscriber)
    assert subscriber.unsubscribed_at is None
    assert subscriber.email == "rider@example.com"
    assert test_db.query(EmailEvent).one().bounce_type == "Temporary"


def test_complaint_stops_sending(client, test_db):
    subscriber, _ = _subscriber_with_send(test_db)

    response = _post(client, _event("email.complained", "re_abc"))

    assert response.json()["result"] == "suppressed"
    test_db.refresh(subscriber)
    assert subscriber.unsubscribed_at is not None
    assert subscriber.email is None
    stats = client.get("/api/admin/notifications", headers=ADMIN).json()
    assert stats["complained"] == 1
    assert stats["recent"][0]["delivery_status"] == "complained"


def test_complaint_matches_subscriber_by_address_when_message_is_unknown(client, test_db):
    # Signup confirmations have no notifications_sent row, so the recipient
    # address is the only link back to the subscriber.
    subscriber = Subscriber(
        name="New",
        email="New.Person@Example.com",
        notification_preference="email",
        unsubscribe_token="token-new",
        confirmed=False,
    )
    test_db.add(subscriber)
    test_db.commit()
    test_db.refresh(subscriber)

    response = _post(
        client, _event("email.complained", "re_unknown", to="new.person@example.com")
    )

    assert response.json()["result"] == "suppressed"
    test_db.refresh(subscriber)
    assert subscriber.unsubscribed_at is not None
    assert subscriber.email is None
    event = test_db.query(EmailEvent).one()
    assert event.notification_id is None
    assert event.subscriber_id == subscriber.id


def test_suppressed_subscriber_gets_no_further_alerts(client, test_db):
    from app.services.king_tide_detector import send_alerts
    import asyncio

    _subscriber_with_send(test_db)
    _post(client, _event("email.bounced", "re_abc", bounce=PERMANENT))

    plan = asyncio.run(send_alerts(test_db, dry_run=True))

    assert plan.subscriber_count == 0
