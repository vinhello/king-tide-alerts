"""NOTIFICATIONS_ENABLED: when false, nothing leaves the system."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.config import settings
from app.services.notification import send_email, send_sms


@pytest.fixture
def notifications_disabled():
    original = settings.NOTIFICATIONS_ENABLED
    settings.NOTIFICATIONS_ENABLED = False
    yield
    settings.NOTIFICATIONS_ENABLED = original


def test_send_email_skips_provider_when_disabled(notifications_disabled):
    with patch("app.services.notification.resend.Emails.send") as mock_resend:
        asyncio.run(send_email("rider@example.com", "Subject", "<p>hi</p>"))
    mock_resend.assert_not_called()


def test_send_sms_skips_provider_when_disabled(notifications_disabled):
    with patch("app.services.notification._get_twilio_client") as get_client:
        asyncio.run(send_sms("+14155550100", "hello"))
    get_client.assert_not_called()


def test_send_email_uses_provider_when_enabled():
    assert settings.NOTIFICATIONS_ENABLED is True
    with patch("app.services.notification.resend.Emails.send") as mock_resend:
        asyncio.run(send_email("rider@example.com", "Subject", "<p>hi</p>"))
    mock_resend.assert_called_once()


def test_send_sms_uses_provider_when_enabled():
    client = MagicMock()
    with patch("app.services.notification._get_twilio_client", return_value=client):
        asyncio.run(send_sms("+14155550100", "hello"))
    client.messages.create.assert_called_once()
