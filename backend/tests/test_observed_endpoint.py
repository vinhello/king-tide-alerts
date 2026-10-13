"""GET /api/tides/observed: measured levels next to predictions, cached."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services import recent_tides

OBS = [
    {"datetime": "2026-10-12 10:00", "height": 5.1},
    {"datetime": "2026-10-12 11:00", "height": 5.6},
]
PRED = [
    {"datetime": "2026-10-12 10:00", "height": 4.4},
    {"datetime": "2026-10-12 11:00", "height": 4.9},
    {"datetime": "2026-10-12 12:00", "height": 5.2},  # after the newest observation
]


@pytest.fixture(autouse=True)
def clear_cache():
    recent_tides.clear_cache()
    yield
    recent_tides.clear_cache()


def _noaa(obs=OBS, pred=PRED):
    return (
        patch(
            "app.services.recent_tides.noaa.fetch_hourly_observations",
            new_callable=AsyncMock,
            return_value=obs,
        ),
        patch(
            "app.services.recent_tides.noaa.fetch_hourly_predictions_between",
            new_callable=AsyncMock,
            return_value=pred,
        ),
    )


def test_observed_returns_both_series_trimmed_to_observations(client):
    obs_patch, pred_patch = _noaa()
    with obs_patch, pred_patch:
        response = client.get("/api/tides/observed?days=3")

    assert response.status_code == 200
    data = response.json()
    assert [o["height"] for o in data["observations"]] == [5.1, 5.6]
    # The prediction for an hour with no observation yet is dropped.
    assert [p["datetime"] for p in data["predictions"]] == [
        "2026-10-12 10:00",
        "2026-10-12 11:00",
    ]
    assert data["as_of"] == "2026-10-12 11:00"
    assert data["days"] == 3
    assert data["station_id"]


def test_observed_is_cached_per_window(client):
    obs_patch, pred_patch = _noaa()
    with obs_patch as obs_mock, pred_patch:
        client.get("/api/tides/observed?days=3")
        client.get("/api/tides/observed?days=3")
        client.get("/api/tides/observed?days=2")
    assert obs_mock.await_count == 2


def test_observed_without_data_is_empty_not_an_error(client):
    obs_patch, pred_patch = _noaa(obs=[], pred=[])
    with obs_patch, pred_patch:
        response = client.get("/api/tides/observed")

    assert response.status_code == 200
    assert response.json()["observations"] == []
    assert response.json()["predictions"] == []
    assert response.json()["as_of"] == ""


def test_observed_keeps_last_good_series_when_noaa_fails(client, monkeypatch):
    monkeypatch.setattr(recent_tides, "CACHE_SECONDS", 0)
    obs_patch, pred_patch = _noaa()
    with obs_patch, pred_patch:
        client.get("/api/tides/observed?days=3")
    obs_patch, pred_patch = _noaa(obs=[], pred=[])
    with obs_patch, pred_patch:
        response = client.get("/api/tides/observed?days=3")

    assert [o["height"] for o in response.json()["observations"]] == [5.1, 5.6]


def test_observed_days_are_bounded(client):
    assert client.get("/api/tides/observed?days=0").status_code == 422
    assert client.get("/api/tides/observed?days=8").status_code == 422
