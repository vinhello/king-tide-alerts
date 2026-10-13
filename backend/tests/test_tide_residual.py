from unittest.mock import AsyncMock, patch

import pytest

from app.config import settings
from app.services import tide_residual
from app.services.tide_residual import (
    MIN_SAMPLE_HOURS,
    ResidualSummary,
    compute_residual,
    get_residual_summary,
)
from app.utils.email_templates import residual_sentence


def _series(hours: int, obs_offset: float, start_day: int = 1):
    """Hourly predictions and observations offset by a constant, over N hours."""
    preds, obs = [], []
    for i in range(hours):
        day = start_day + i // 24
        stamp = f"2026-10-{day:02d} {i % 24:02d}:00"
        preds.append({"datetime": stamp, "height": 4.0})
        obs.append({"datetime": stamp, "height": 4.0 + obs_offset})
    return obs, preds


def test_compute_residual_mean_over_matched_hours():
    obs, preds = _series(72, obs_offset=0.8)
    # Extra observation with no matching prediction must be ignored.
    obs.append({"datetime": "2026-10-20 00:06", "height": 9.9})
    summary = compute_residual(obs, preds, window_days=30)

    assert summary is not None
    assert summary.mean_residual_ft == 0.8
    assert summary.sample_hours == 72
    assert summary.window_days == 30
    assert summary.as_of == "2026-10-03"


def test_compute_residual_handles_negative_and_rounds():
    obs, preds = _series(60, obs_offset=-0.237)
    summary = compute_residual(obs, preds, window_days=30)
    assert summary is not None
    assert summary.mean_residual_ft == -0.24


def test_compute_residual_requires_minimum_samples():
    obs, preds = _series(MIN_SAMPLE_HOURS - 1, obs_offset=1.0)
    assert compute_residual(obs, preds, window_days=30) is None


def test_compute_residual_with_no_overlap_is_none():
    obs, _ = _series(72, obs_offset=1.0)
    _, preds = _series(72, obs_offset=0.0, start_day=20)
    assert compute_residual(obs, preds, window_days=30) is None


@pytest.fixture
def clear_cache():
    tide_residual.clear_cache()
    yield
    tide_residual.clear_cache()


@pytest.mark.asyncio
async def test_get_residual_summary_fetches_and_caches(clear_cache):
    obs, preds = _series(72, obs_offset=0.5)
    with (
        patch(
            "app.services.tide_residual.noaa.fetch_hourly_observations",
            new_callable=AsyncMock,
            return_value=obs,
        ) as fetch_obs,
        patch(
            "app.services.tide_residual.noaa.fetch_hourly_predictions_between",
            new_callable=AsyncMock,
            return_value=preds,
        ) as fetch_pred,
    ):
        first = await get_residual_summary()
        second = await get_residual_summary()

    assert first is not None and first.mean_residual_ft == 0.5
    assert second is first
    assert fetch_obs.await_count == 1
    assert fetch_pred.await_count == 1


@pytest.mark.asyncio
async def test_get_residual_summary_refetches_after_cache_expiry(clear_cache):
    obs, preds = _series(72, obs_offset=0.5)
    original = settings.RESIDUAL_CACHE_SECONDS
    settings.RESIDUAL_CACHE_SECONDS = 0
    try:
        with (
            patch(
                "app.services.tide_residual.noaa.fetch_hourly_observations",
                new_callable=AsyncMock,
                return_value=obs,
            ) as fetch_obs,
            patch(
                "app.services.tide_residual.noaa.fetch_hourly_predictions_between",
                new_callable=AsyncMock,
                return_value=preds,
            ),
        ):
            await get_residual_summary()
            await get_residual_summary()
    finally:
        settings.RESIDUAL_CACHE_SECONDS = original

    assert fetch_obs.await_count == 2


@pytest.mark.asyncio
async def test_get_residual_summary_is_none_when_noaa_returns_nothing(clear_cache):
    with (
        patch(
            "app.services.tide_residual.noaa.fetch_hourly_observations",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "app.services.tide_residual.noaa.fetch_hourly_predictions_between",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        assert await get_residual_summary() is None


@pytest.mark.asyncio
async def test_get_residual_summary_keeps_last_good_value_on_failure(clear_cache):
    obs, preds = _series(72, obs_offset=0.5)
    original = settings.RESIDUAL_CACHE_SECONDS
    settings.RESIDUAL_CACHE_SECONDS = 0
    try:
        with (
            patch(
                "app.services.tide_residual.noaa.fetch_hourly_observations",
                new_callable=AsyncMock,
                side_effect=[obs, []],
            ),
            patch(
                "app.services.tide_residual.noaa.fetch_hourly_predictions_between",
                new_callable=AsyncMock,
                return_value=preds,
            ),
        ):
            good = await get_residual_summary()
            after_failure = await get_residual_summary()
    finally:
        settings.RESIDUAL_CACHE_SECONDS = original

    assert good is not None
    assert after_failure is good


def test_residual_sentence_above_below_matched_and_none():
    above = ResidualSummary(mean_residual_ft=0.77, sample_hours=700, window_days=30, as_of="2026-10-12")
    below = ResidualSummary(mean_residual_ft=-0.3, sample_hours=700, window_days=30, as_of="2026-10-12")
    flat = ResidualSummary(mean_residual_ft=0.02, sample_hours=700, window_days=30, as_of="2026-10-12")

    assert "averaged 0.8 ft above NOAA's predictions" in residual_sentence(above)
    assert "30 days ending 2026-10-12" in residual_sentence(above)
    assert "averaged 0.3 ft below" in residual_sentence(below)
    assert "matched NOAA's predictions" in residual_sentence(flat)
    assert residual_sentence(None) == ""
    for text in (residual_sentence(above), residual_sentence(below)):
        assert "expect" not in text.lower()
        assert " will " not in text.lower()


def test_current_tide_includes_residual_when_available(client):
    summary = ResidualSummary(mean_residual_ft=0.77, sample_hours=714, window_days=30, as_of="2026-10-12")
    with (
        patch(
            "app.routers.tides.fetch_current_water_level",
            new_callable=AsyncMock,
            return_value={"height": 4.0, "timestamp": "2026-10-12 10:00"},
        ),
        patch("app.routers.tides.fetch_next_high_tide", new_callable=AsyncMock, return_value=None),
        patch(
            "app.routers.tides.get_residual_summary",
            new_callable=AsyncMock,
            return_value=summary,
        ),
    ):
        response = client.get("/api/tides/current")

    data = response.json()
    assert data["residual_ft"] == 0.77
    assert data["residual_window_days"] == 30
    assert data["residual_sample_hours"] == 714
    assert data["residual_as_of"] == "2026-10-12"


def test_current_tide_omits_residual_when_unavailable(client):
    with (
        patch(
            "app.routers.tides.fetch_current_water_level",
            new_callable=AsyncMock,
            return_value={"height": 4.0, "timestamp": "2026-10-12 10:00"},
        ),
        patch("app.routers.tides.fetch_next_high_tide", new_callable=AsyncMock, return_value=None),
    ):
        response = client.get("/api/tides/current")

    data = response.json()
    assert data["residual_ft"] is None
    assert data["residual_as_of"] is None


def test_alert_email_includes_residual_sentence_only_when_given():
    from app.utils.email_templates import king_tide_alert_email

    kwargs = dict(
        name="Vince", date_range="Tuesday, November 24", peak_date="Tuesday, November 24",
        peak_time="10:59 AM", flood_window_start="8:59 AM", flood_window_end="12:59 PM",
        height=6.8, is_king_tide=True, is_multi_day=False, days_until=7,
        unsubscribe_url="https://kingtidealert.com/unsubscribe/x",
    )
    without = king_tide_alert_email(**kwargs)
    with_residual = king_tide_alert_email(
        **kwargs,
        residual=ResidualSummary(mean_residual_ft=0.9, sample_hours=700, window_days=30, as_of="2026-11-17"),
    )
    assert "Measured recently" not in without
    assert "Measured recently" in with_residual
    assert "averaged 0.9 ft above" in with_residual
