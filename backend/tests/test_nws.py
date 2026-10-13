"""NWS coastal flood relay: parsing, filtering, caching and the endpoint.

The fixture is a trimmed real response from api.weather.gov captured on
2026-10-13 for zones CAZ505, CAZ506 and CAZ508 (two advisories in effect).
"""

import copy
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.services import nws

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "nws_alerts.json").read_text())
FEATURES = FIXTURE["features"]
OUR_ZONES = ["CAZ505", "CAZ506", "CAZ508"]


@pytest.fixture(autouse=True)
def clear_cache():
    nws.clear_cache()
    yield
    nws.clear_cache()


def _fetch(return_value):
    return patch(
        "app.services.nws.fetch_active_alerts", new_callable=AsyncMock, return_value=return_value
    )


def _variant(feature, **props):
    copied = copy.deepcopy(feature)
    copied["properties"].update(props)
    return copied


# --- parsing ----------------------------------------------------------------


def test_parse_bullets_joins_wrapped_lines():
    description = FEATURES[0]["properties"]["description"]
    bullets = nws.parse_bullets(description)

    assert set(bullets) >= {"WHAT", "WHERE", "WHEN", "IMPACTS"}
    assert bullets["WHAT"].startswith("Up to")
    assert "\n" not in bullets["WHAT"]
    assert "  " not in bullets["WHAT"]


def test_parse_alert_quotes_nws_and_links_to_our_zone():
    alert = nws.parse_alert(FEATURES[0], OUR_ZONES)

    assert alert is not None
    assert alert.event == "Coastal Flood Advisory"
    assert alert.sender_name.startswith("NWS")
    assert alert.what and alert.when and alert.headline
    assert alert.ends.startswith("2026-")
    assert alert.zones and set(alert.zones) <= set(OUR_ZONES)
    assert alert.link == f"https://forecast.weather.gov/MapClick.php?zoneid={alert.zones[0]}"


def test_parse_alert_drops_other_events_and_test_messages():
    assert nws.parse_alert(_variant(FEATURES[0], event="Wind Advisory"), OUR_ZONES) is None
    assert nws.parse_alert(_variant(FEATURES[0], status="Test"), OUR_ZONES) is None


def test_parse_alert_without_our_zone_falls_back_to_office_link():
    feature = _variant(FEATURES[0], geocode={"UGC": ["CAZ006"]})
    alert = nws.parse_alert(feature, OUR_ZONES)
    assert alert is not None
    assert alert.zones == []
    assert alert.link == nws.NWS_FALLBACK_LINK


# --- selection and caching --------------------------------------------------


@pytest.mark.asyncio
async def test_alerts_are_filtered_deduplicated_and_ranked():
    warning = _variant(FEATURES[0], id="urn:test:warning", event="Coastal Flood Warning")
    wind = _variant(FEATURES[0], id="urn:test:wind", event="Wind Advisory")
    features = [FEATURES[0], FEATURES[0], wind, warning] + FEATURES[1:]

    with _fetch(features):
        alerts = await nws.get_coastal_flood_alerts()

    ids = [a.id for a in alerts]
    assert ids[0] == "urn:test:warning"
    assert len(ids) == len(set(ids)) == 1 + len(FEATURES)
    assert all("coastal flood" in a.event.lower() for a in alerts)


def test_endpoint_returns_alerts_and_caches(client):
    with _fetch(FEATURES) as fetch:
        first = client.get("/api/alerts/nws")
        second = client.get("/api/alerts/nws")

    assert first.status_code == 200
    data = first.json()
    assert data["zones"] == OUR_ZONES
    assert len(data["alerts"]) == len(FEATURES)
    alert = data["alerts"][0]
    for key in ("event", "what", "when", "ends", "sender_name", "link", "headline"):
        assert alert[key]
    assert second.json() == data
    assert fetch.await_count == 1


def test_endpoint_is_empty_when_nothing_is_in_effect(client):
    with _fetch([]):
        response = client.get("/api/alerts/nws")
    assert response.status_code == 200
    assert response.json()["alerts"] == []


def test_endpoint_is_empty_when_nws_is_unreachable_and_nothing_cached(client):
    with _fetch(None):
        response = client.get("/api/alerts/nws")
    assert response.status_code == 200
    assert response.json()["alerts"] == []


def test_last_list_is_served_briefly_when_nws_is_unreachable(client, monkeypatch):
    monkeypatch.setattr(nws.settings, "NWS_CACHE_SECONDS", 0)
    far_future = _variant(FEATURES[0], ends="2999-01-01T00:00:00-08:00")
    ended = _variant(FEATURES[0], id="urn:test:ended", ends="2000-01-01T00:00:00-08:00")
    with _fetch([far_future, ended]):
        assert len(client.get("/api/alerts/nws").json()["alerts"]) == 2
    with _fetch(None):
        alerts = client.get("/api/alerts/nws").json()["alerts"]
    # Still shown while fresh enough, minus the one that has ended.
    assert [a["id"] for a in alerts] == [far_future["properties"]["id"]]

    monkeypatch.setattr(nws, "STALE_MAX_SECONDS", 0)
    with _fetch(None):
        assert client.get("/api/alerts/nws").json()["alerts"] == []
