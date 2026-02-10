from unittest.mock import AsyncMock, patch


def test_upcoming_tides_returns_predictions(client):
    """GET /api/tides/upcoming should return tide predictions."""
    mock_predictions = [
        {"datetime": "2026-02-10 01:41", "height": 6.8, "type": "H"},
        {"datetime": "2026-02-10 08:12", "height": 0.3, "type": "L"},
        {"datetime": "2026-02-10 14:23", "height": 5.2, "type": "H"},
        {"datetime": "2026-02-10 20:45", "height": 1.2, "type": "L"},
    ]

    with patch(
        "app.routers.tides.fetch_all_tide_predictions",
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
        {"datetime": "2026-02-10 01:41", "height": 7.1, "type": "H"},
        {"datetime": "2026-02-10 08:12", "height": 0.3, "type": "L"},
        {"datetime": "2026-02-10 14:23", "height": 6.5, "type": "H"},
        {"datetime": "2026-02-10 20:45", "height": 1.2, "type": "L"},
        {"datetime": "2026-02-11 02:15", "height": 6.2, "type": "H"},
        {"datetime": "2026-02-11 15:01", "height": 5.8, "type": "H"},
    ]

    with patch(
        "app.routers.tides.fetch_all_tide_predictions",
        new_callable=AsyncMock,
        return_value=mock_predictions,
    ):
        response = client.get("/api/tides/upcoming")

    data = response.json()
    predictions = data["predictions"]

    # 7.1 >= 6.5 king tide threshold
    assert predictions[0]["is_king_tide"] is True
    # 0.3 low tide - not king tide
    assert predictions[1]["is_king_tide"] is False
    # 6.5 >= 6.5 king tide threshold
    assert predictions[2]["is_king_tide"] is True
    # 1.2 low tide - not king tide
    assert predictions[3]["is_king_tide"] is False
    # 6.2 and 5.8 are below king tide threshold
    assert predictions[4]["is_king_tide"] is False
    assert predictions[5]["is_king_tide"] is False
