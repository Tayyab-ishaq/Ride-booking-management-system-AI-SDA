from __future__ import annotations

from uuid import UUID, uuid4

from app.config import Settings, get_settings as real_get_settings
from app.dependencies import get_db as real_get_db
from app.main import app
from core.security import create_access_token
from fastapi.testclient import TestClient


TEST_SETTINGS = Settings(
    database_url="sqlite:///:memory:",
    jwt_secret="test-secret-which-is-long-enough-to-be-safe-123456",
    jwt_algorithm="HS256",
    access_token_expire_minutes=60,
    refresh_token_expire_minutes=10080,
)


class FakeConnection:
    def __init__(self, driver_id: UUID | None = None):
        self.driver_id = driver_id or uuid4()
        self.deleted_locations_for: list[str] = []

    async def fetchrow(self, query: str, *args, **kwargs):
        if "SELECT id FROM drivers" in query:
            if len(args) == 1 and str(args[0]) in {str(self.driver_id), str(uuid4())}:
                return {"id": self.driver_id}
            return {"id": self.driver_id}

        if "INSERT INTO driver_locations" in query:
            return {
                "loc_id": uuid4(),
                "driver_id": self.driver_id,
                "latitude": 51.0,
                "longitude": -0.1,
                "recorded_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            }

        if "UPDATE drivers" in query:
            return {"id": self.driver_id, "is_available": args[1]}

        return None

    async def execute(self, query: str, *args, **kwargs):
        if "DELETE FROM driver_locations" in query:
            self.deleted_locations_for.append(str(args[0]))
        return "OK"


def _make_client(connection: FakeConnection) -> TestClient:
    app.dependency_overrides.clear()
    app.dependency_overrides[real_get_settings] = lambda: TEST_SETTINGS
    app.dependency_overrides[real_get_db] = lambda: connection
    return TestClient(app)


def _make_token(sub: str) -> str:
    return create_access_token(
        {"sub": sub, "role": "driver"},
        TEST_SETTINGS.jwt_secret,
        TEST_SETTINGS.jwt_algorithm,
        TEST_SETTINGS.access_token_expire_minutes,
    )


def test_save_location_returns_404_when_driver_missing():
    class MissingDriverConnection(FakeConnection):
        async def fetchrow(self, query: str, *args, **kwargs):
            if "SELECT id FROM drivers" in query:
                return None
            return await super().fetchrow(query, *args, **kwargs)

    client = _make_client(MissingDriverConnection())
    token = _make_token(str(uuid4()))

    response = client.post(
        "/api/driver/save-location",
        headers={"Authorization": f"Bearer {token}"},
        json={"latitude": 51.0, "longitude": -0.1},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Driver profile not found. Register as a driver first."


def test_delete_locations_removes_rows_for_authenticated_driver():
    connection = FakeConnection()
    client = _make_client(connection)
    token = _make_token(str(connection.driver_id))

    response = client.delete(
        "/api/driver/locations",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Driver locations deleted"
    assert connection.deleted_locations_for == [str(connection.driver_id)]
