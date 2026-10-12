from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.config import settings
from app.services.healthcheck import HealthcheckSignal, ping_healthcheck, ping_url_for

PING_URL = "https://hc-ping.com/00000000-0000-0000-0000-000000000000"


@pytest.fixture
def ping_url(request):
    """Set HEALTHCHECK_PING_URL for one test and restore it afterwards."""
    value = getattr(request, "param", PING_URL)
    original = settings.HEALTHCHECK_PING_URL
    settings.HEALTHCHECK_PING_URL = value
    yield value
    settings.HEALTHCHECK_PING_URL = original


def _mock_client(get_side_effect=None):
    response = MagicMock()
    response.raise_for_status = MagicMock()
    client = AsyncMock()
    client.get.return_value = response
    if get_side_effect is not None:
        client.get.side_effect = get_side_effect
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


def test_ping_url_for_each_signal():
    assert ping_url_for(PING_URL, HealthcheckSignal.SUCCESS) == PING_URL
    assert ping_url_for(PING_URL, HealthcheckSignal.START) == PING_URL + "/start"
    assert ping_url_for(PING_URL, HealthcheckSignal.FAIL) == PING_URL + "/fail"


def test_ping_url_for_tolerates_trailing_slash():
    assert ping_url_for(PING_URL + "/", HealthcheckSignal.FAIL) == PING_URL + "/fail"


@pytest.mark.asyncio
@pytest.mark.parametrize("ping_url", [""], indirect=True)
async def test_ping_is_noop_when_url_unset(ping_url):
    with patch("app.services.healthcheck.httpx.AsyncClient") as mock_client_cls:
        await ping_healthcheck(HealthcheckSignal.SUCCESS)

    mock_client_cls.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "signal,expected_url",
    [
        (HealthcheckSignal.SUCCESS, PING_URL),
        (HealthcheckSignal.START, PING_URL + "/start"),
        (HealthcheckSignal.FAIL, PING_URL + "/fail"),
    ],
)
async def test_ping_requests_the_signal_url(ping_url, signal, expected_url):
    client = _mock_client()
    with patch("app.services.healthcheck.httpx.AsyncClient", return_value=client):
        await ping_healthcheck(signal)

    client.get.assert_called_once()
    assert client.get.call_args.args[0] == expected_url


@pytest.mark.asyncio
async def test_ping_network_errors_are_swallowed(ping_url):
    client = _mock_client(get_side_effect=httpx.ConnectError("monitor unreachable"))
    with patch("app.services.healthcheck.httpx.AsyncClient", return_value=client):
        await ping_healthcheck(HealthcheckSignal.SUCCESS)  # must not raise


@pytest.mark.asyncio
async def test_ping_http_errors_are_swallowed(ping_url):
    client = _mock_client()
    client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500", request=MagicMock(), response=MagicMock()
    )
    with patch("app.services.healthcheck.httpx.AsyncClient", return_value=client):
        await ping_healthcheck(HealthcheckSignal.FAIL)  # must not raise
