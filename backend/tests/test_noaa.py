from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.noaa import fetch_tide_predictions, get_king_tides


@pytest.mark.asyncio
async def test_fetch_tide_predictions_parses_response(mock_noaa_response):
    """Should parse NOAA response and return only high tides."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_noaa_response
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.noaa.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await fetch_tide_predictions(days_ahead=7)

    assert len(result) == 5  # 5 high tides, 2 low tides filtered out
    assert all(t["type"] == "H" for t in result)
    assert result[0]["height"] == 1.84
    assert result[0]["datetime"] == "2026-02-10 01:41"


@pytest.mark.asyncio
async def test_get_king_tides_filters_above_threshold(mock_noaa_response):
    """Should return only tides above the king tide threshold."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_noaa_response
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.noaa.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await get_king_tides(days_ahead=7, threshold=1.0)

    assert len(result) == 2  # Only 1.84 and 1.92 are above 1.0
    assert all(t["height"] > 1.0 for t in result)


@pytest.mark.asyncio
async def test_handles_noaa_api_error():
    """Should return empty list on NOAA API errors."""
    import httpx

    with patch("app.services.noaa.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await fetch_tide_predictions(days_ahead=7)

    assert result == []
