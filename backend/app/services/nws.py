"""Active National Weather Service coastal flood products for our zones.

Relay only: the NWS wording is passed through verbatim and attributed to
them. Nothing here interprets or forecasts.
"""

import logging
import re
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"
# Public page for a zone; it lists the hazards in effect at the top.
NWS_ZONE_PAGE = "https://forecast.weather.gov/MapClick.php?zoneid={zone}"
NWS_FALLBACK_LINK = "https://www.weather.gov/mtr/"

COASTAL_FLOOD = "coastal flood"
# Order shown when several products are active at once.
EVENT_RANK = {"warning": 0, "watch": 1, "advisory": 2, "statement": 3}
# Serve a stale list for at most this long when NWS cannot be reached.
STALE_MAX_SECONDS = 3600

# "* WHAT...text" sections; wrapped lines belong to the section above them.
BULLET_PATTERN = re.compile(
    r"\*\s*([A-Z][A-Z ]*?)\.\.\.(.*?)(?=\n\s*\*\s*[A-Z][A-Z ]*?\.\.\.|\Z)", re.S
)


@dataclass(frozen=True)
class NwsAlert:
    id: str
    event: str
    severity: str
    headline: str
    what: str
    where: str
    when: str
    impacts: str
    additional_details: str
    instruction: str
    onset: str
    ends: str
    sent: str
    sender_name: str
    zones: list[str]
    link: str


def zones() -> list[str]:
    return [z.strip().upper() for z in settings.NWS_ZONES.split(",") if z.strip()]


async def fetch_active_alerts(zone_ids: list[str]) -> list[dict[str, Any]] | None:
    """Raw alert features for the zones, or None when NWS could not be reached."""
    params = {"zone": ",".join(zone_ids)}
    headers = {"User-Agent": settings.NWS_USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                NWS_ALERTS_URL, params=params, headers=headers, timeout=15.0
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.error(f"NWS API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching NWS alerts: {e}")
            return None
    features = data.get("features") if isinstance(data, dict) else None
    return features if isinstance(features, list) else []


def parse_bullets(description: str) -> dict[str, str]:
    """WHAT / WHERE / WHEN / IMPACTS / ADDITIONAL DETAILS, wrapped lines joined."""
    sections: dict[str, str] = {}
    for name, body in BULLET_PATTERN.findall(description or ""):
        sections[name.strip()] = " ".join(body.split())
    return sections


def parse_alert(feature: dict[str, Any], our_zones: list[str]) -> NwsAlert | None:
    """One coastal flood product, or None for anything else (including tests)."""
    props = feature.get("properties") or {}
    event = str(props.get("event") or "")
    if COASTAL_FLOOD not in event.lower():
        return None
    if str(props.get("status") or "Actual") != "Actual":
        return None

    ugc = (props.get("geocode") or {}).get("UGC") or []
    matched = [z for z in our_zones if z in ugc]
    bullets = parse_bullets(str(props.get("description") or ""))
    return NwsAlert(
        id=str(props.get("id") or feature.get("id") or ""),
        event=event,
        severity=str(props.get("severity") or ""),
        headline=str(props.get("headline") or ""),
        what=bullets.get("WHAT", ""),
        where=bullets.get("WHERE", ""),
        when=bullets.get("WHEN", ""),
        impacts=bullets.get("IMPACTS", ""),
        additional_details=bullets.get("ADDITIONAL DETAILS", ""),
        instruction=" ".join(str(props.get("instruction") or "").split()),
        onset=str(props.get("onset") or props.get("effective") or ""),
        ends=str(props.get("ends") or props.get("expires") or ""),
        sent=str(props.get("sent") or ""),
        sender_name=str(props.get("senderName") or "National Weather Service"),
        zones=matched,
        link=NWS_ZONE_PAGE.format(zone=matched[0]) if matched else NWS_FALLBACK_LINK,
    )


def collapse_by_event(alerts: list[NwsAlert]) -> list[NwsAlert]:
    """One alert per event name.

    NWS issues a separate product per zone group, so the same advisory for
    the Bay shoreline and for the Marin coast arrives as two ids with the
    same text. Riders should see it once: the product ending last stands in
    for the group, and the zones are the union of all of them.
    """
    groups: dict[str, list[NwsAlert]] = {}
    for alert in alerts:
        groups.setdefault(alert.event, []).append(alert)
    merged = []
    for group in groups.values():
        representative = max(group, key=lambda a: a.ends)
        zones = sorted({z for a in group for z in a.zones})
        link = representative.link
        if not representative.zones and zones:
            link = NWS_ZONE_PAGE.format(zone=zones[0])
        merged.append(replace(representative, zones=zones, link=link))
    return merged


def _rank(alert: NwsAlert) -> tuple[int, str]:
    kind = alert.event.lower().rsplit(" ", 1)[-1]
    return (EVENT_RANK.get(kind, 9), alert.ends)


def _still_in_effect(alert: NwsAlert, now: datetime) -> bool:
    try:
        return datetime.fromisoformat(alert.ends) > now
    except ValueError:
        return True


_cache: tuple[float, list[NwsAlert]] | None = None


async def get_coastal_flood_alerts() -> list[NwsAlert]:
    """Active coastal flood products for our zones, deduplicated and ranked.

    Cached for NWS_CACHE_SECONDS. When NWS cannot be reached the last list
    is served for up to STALE_MAX_SECONDS, minus anything that has ended;
    after that nothing is shown rather than something possibly wrong.
    """
    global _cache
    now = time.monotonic()
    if _cache is not None and now - _cache[0] < settings.NWS_CACHE_SECONDS:
        return _cache[1]

    our_zones = zones()
    features = await fetch_active_alerts(our_zones)
    if features is None:
        if _cache is not None and now - _cache[0] < STALE_MAX_SECONDS:
            wall_now = datetime.now(timezone.utc)
            return [a for a in _cache[1] if _still_in_effect(a, wall_now)]
        return []

    alerts: dict[str, NwsAlert] = {}
    for feature in features:
        alert = parse_alert(feature, our_zones)
        if alert is not None and alert.id not in alerts:
            alerts[alert.id] = alert
    result = sorted(collapse_by_event(list(alerts.values())), key=_rank)
    _cache = (now, result)
    if result:
        logger.info("NWS in effect: " + "; ".join(f"{a.event} until {a.ends}" for a in result))
    return result


def clear_cache() -> None:
    """For tests."""
    global _cache
    _cache = None
