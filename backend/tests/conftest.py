import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.config import settings
from app.database import Base, get_db
from app.main import app

# Set admin password for tests
settings.ADMIN_PASSWORD = "test-password"


# Use SQLite in-memory for tests
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def test_db():
    """Create tables before each test, drop after."""
    # SQLite doesn't support PostgreSQL UUID type, so we need to handle this
    # by creating tables directly from metadata
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """FastAPI test client with DB override."""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_noaa_response():
    """Sample NOAA API JSON response (hilo interval)."""
    return {
        "predictions": [
            {"t": "2026-02-10 01:41", "v": "6.8", "type": "H"},
            {"t": "2026-02-10 14:23", "v": "5.2", "type": "H"},
            {"t": "2026-02-11 02:15", "v": "7.1", "type": "H"},
            {"t": "2026-02-11 15:01", "v": "4.5", "type": "H"},
            {"t": "2026-02-12 03:00", "v": "5.8", "type": "H"},
            {"t": "2026-02-10 08:12", "v": "0.3", "type": "L"},
            {"t": "2026-02-10 20:45", "v": "1.2", "type": "L"},
        ],
    }


@pytest.fixture
def mock_hourly_noaa_response():
    """Sample NOAA API JSON response (hourly interval)."""
    return {
        "predictions": [
            {"t": "2026-02-10 00:00", "v": "5.2"},
            {"t": "2026-02-10 01:00", "v": "6.1"},
            {"t": "2026-02-10 02:00", "v": "6.8"},
            {"t": "2026-02-10 03:00", "v": "6.3"},
        ],
    }
