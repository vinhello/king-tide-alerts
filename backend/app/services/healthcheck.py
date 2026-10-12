"""Dead man's switch pings for the daily alert job.

The scheduler tells an external monitor (healthchecks.io) when the daily run
starts, succeeds or fails. If the monitor stops hearing from us by the
deadline it configures, it emails the operator. Every call here is
best-effort: a monitoring problem must never break the alert run itself.
"""

import enum
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

PING_TIMEOUT_SECONDS = 10.0


class HealthcheckSignal(str, enum.Enum):
    START = "start"
    SUCCESS = "success"
    FAIL = "fail"


def ping_url_for(base_url: str, signal: HealthcheckSignal) -> str:
    """Build the URL for a signal. Success pings the base URL itself."""
    base = base_url.rstrip("/")
    if signal is HealthcheckSignal.SUCCESS:
        return base
    return f"{base}/{signal.value}"


async def ping_healthcheck(signal: HealthcheckSignal) -> None:
    """Send one signal to the monitor. Does nothing when no URL is configured."""
    base_url = settings.HEALTHCHECK_PING_URL
    if not base_url:
        return

    url = ping_url_for(base_url, signal)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=PING_TIMEOUT_SECONDS)
            response.raise_for_status()
        logger.info(f"Healthcheck ping sent: {signal.value}")
    except Exception as e:
        # Never let monitoring failures affect the job. The URL is not
        # logged because it is the credential for this check.
        logger.error(f"Healthcheck ping failed ({signal.value}): {e}")
