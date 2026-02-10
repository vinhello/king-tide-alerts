from unittest.mock import AsyncMock, patch


def test_upcoming_tides_returns_predictions(client):
    """GET /api/tides/upcoming should return tide predictions."""
    mock_predictions = [
        {"datetime": "2026-02-10 00:00", "height": 5.2},
        {"datetime": "2026-02-10 01:00", "height": 6.1},
        {"datetime": "2026-02-10 02:00", "height": 6.8},
        {"datetime": "2026-02-10 03:00", "height": 6.3},
    ]

    with patch(
        "app.routers.tides.fetch_hourly_tide_predictions",
        new_callable=AsyncMock,
        return_value=mock_predictions,
    ):
        response = client.get("/api/tides/upcoming?days=7")

    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 4
    assert "threshold" in data
    assert "station_id" in data


def test_king_tide_flag_set_correctly(client):
    """Predictions at/above 6.5 ft should have is_king_tide=True."""
    mock_predictions = [
        {"datetime": "2026-02-10 00:00", "height": 7.1},
        {"datetime": "2026-02-10 01:00", "height": 6.5},
        {"datetime": "2026-02-10 02:00", "height": 6.2},
        {"datetime": "2026-02-10 03:00", "height": 5.8},
    ]

    with patch(
        "app.routers.tides.fetch_hourly_tide_predictions",
        new_callable=AsyncMock,
        return_value=mock_predictions,
    ):
        response = client.get("/api/tides/upcoming")

    data = response.json()
    predictions = data["predictions"]

    # 7.1 >= 6.5 king tide threshold
    assert predictions[0]["is_king_tide"] is True
    # 6.5 >= 6.5 king tide threshold
    assert predictions[1]["is_king_tide"] is True
    # 6.2 and 5.8 are below king tide threshold
    assert predictions[2]["is_king_tide"] is False
    assert predictions[3]["is_king_tide"] is False
