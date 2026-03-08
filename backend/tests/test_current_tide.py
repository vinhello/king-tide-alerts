from unittest.mock import AsyncMock, patch


def test_current_tide_safe(client):
    mock_water_level = {"height": 4.0, "timestamp": "2026-03-08 10:00"}
    mock_next_high = {"datetime": "2026-03-08 18:00", "height": 6.2}

    with (
        patch(
            "app.routers.tides.fetch_current_water_level",
            new_callable=AsyncMock,
            return_value=mock_water_level,
        ),
        patch(
            "app.routers.tides.fetch_next_high_tide",
            new_callable=AsyncMock,
            return_value=mock_next_high,
        ),
    ):
        response = client.get("/api/tides/current")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "safe"
    assert data["current_height"] == 4.0


def test_current_tide_caution(client):
    mock_water_level = {"height": 5.2, "timestamp": "2026-03-08 10:00"}
    mock_next_high = {"datetime": "2026-03-08 18:00", "height": 6.5}

    with (
        patch(
            "app.routers.tides.fetch_current_water_level",
            new_callable=AsyncMock,
            return_value=mock_water_level,
        ),
        patch(
            "app.routers.tides.fetch_next_high_tide",
            new_callable=AsyncMock,
            return_value=mock_next_high,
        ),
    ):
        response = client.get("/api/tides/current")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "caution"
    assert data["current_height"] == 5.2


def test_current_tide_flooded(client):
    mock_water_level = {"height": 6.1, "timestamp": "2026-03-08 10:00"}
    mock_next_high = None

    with (
        patch(
            "app.routers.tides.fetch_current_water_level",
            new_callable=AsyncMock,
            return_value=mock_water_level,
        ),
        patch(
            "app.routers.tides.fetch_next_high_tide",
            new_callable=AsyncMock,
            return_value=mock_next_high,
        ),
    ):
        response = client.get("/api/tides/current")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "flooded"
    assert data["current_height"] == 6.1


def test_current_tide_noaa_error(client):
    with patch(
        "app.routers.tides.fetch_current_water_level",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = client.get("/api/tides/current")

    assert response.status_code == 503


def test_current_tide_hours_calculation(client):
    mock_water_level = {"height": 4.0, "timestamp": "2026-03-08 10:00"}
    mock_next_high = {"datetime": "2026-03-08 16:00", "height": 6.8}

    with (
        patch(
            "app.routers.tides.fetch_current_water_level",
            new_callable=AsyncMock,
            return_value=mock_water_level,
        ),
        patch(
            "app.routers.tides.fetch_next_high_tide",
            new_callable=AsyncMock,
            return_value=mock_next_high,
        ),
    ):
        response = client.get("/api/tides/current")

    assert response.status_code == 200
    data = response.json()
    assert data["hours_until_high_tide"] is not None
    assert data["hours_until_high_tide"] == 6.0
