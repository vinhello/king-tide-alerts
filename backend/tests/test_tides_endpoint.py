from unittest.mock import AsyncMock, patch


def test_upcoming_tides_returns_predictions(client):
    """GET /api/tides/upcoming should return tide predictions."""
    mock_predictions = [
        {"datetime": "2026-02-10 01:41", "height": 1.84, "type": "H"},
        {"datetime": "2026-02-10 14:23", "height": 0.52, "type": "H"},
    ]

    with patch(
        "app.routers.tides.fetch_tide_predictions",
        new_callable=AsyncMock,
        return_value=mock_predictions,
    ):
        response = client.get("/api/tides/upcoming?days=7")

    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 2
    assert "threshold" in data
    assert "station_id" in data


def test_king_tide_flag_set_correctly(client):
    """Predictions above threshold should have is_king_tide=True."""
    mock_predictions = [
        {"datetime": "2026-02-10 01:41", "height": 1.84, "type": "H"},
        {"datetime": "2026-02-10 14:23", "height": 0.52, "type": "H"},
        {"datetime": "2026-02-11 02:15", "height": 0.80, "type": "H"},
    ]

    with patch(
        "app.routers.tides.fetch_tide_predictions",
        new_callable=AsyncMock,
        return_value=mock_predictions,
    ):
        response = client.get("/api/tides/upcoming")

    data = response.json()
    predictions = data["predictions"]

    # 1.84 > 1.0 threshold
    assert predictions[0]["is_king_tide"] is True
    # 0.52 and 0.80 are below threshold
    assert predictions[1]["is_king_tide"] is False
    assert predictions[2]["is_king_tide"] is False
