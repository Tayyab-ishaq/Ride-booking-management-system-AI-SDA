from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.config import Settings
from core.enums import RideStatus, UserRole
from models.ride import Ride
from services.rides.history import RideHistoryService


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _ride(rider_id: UUID, driver_id: UUID | None = None) -> Ride:
    now = datetime.now(timezone.utc)
    return Ride(
        id=uuid4(),
        rider_id=rider_id,
        driver_id=driver_id,
        status=RideStatus.completed,
        origin="A",
        destination="B",
        fare=None,
        rating=None,
        created_at=now,
        updated_at=now,
    )


@dataclass
class FakeRideRepository:
    rider_rides: list[Ride] = field(default_factory=list)
    driver_rides: list[Ride] = field(default_factory=list)

    async def get_history_by_rider(
        self, rider_id: UUID, limit: int, offset: int
    ) -> tuple[list[Ride], int]:
        filtered = [r for r in self.rider_rides if r.rider_id == rider_id]
        return filtered[offset: offset + limit], len(filtered)

    async def get_history_by_driver(
        self, driver_id: UUID, limit: int, offset: int
    ) -> tuple[list[Ride], int]:
        filtered = [r for r in self.driver_rides if r.driver_id == driver_id]
        return filtered[offset: offset + limit], len(filtered)


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

@pytest.fixture()
def settings() -> Settings:
    return Settings(
        database_url="postgresql://localhost/test",
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        access_token_expire_minutes=60,
        refresh_token_expire_minutes=10080,
    )


@pytest.fixture()
def repo() -> FakeRideRepository:
    return FakeRideRepository()


# ------------------------------------------------------------------ #
# Tests                                                                #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio()
async def test_rider_history_returns_correct_rides(
    repo: FakeRideRepository, settings: Settings
) -> None:
    rider_id = uuid4()
    other_id = uuid4()
    repo.rider_rides = [_ride(rider_id), _ride(rider_id), _ride(other_id)]

    rides, total = await RideHistoryService(repo, settings).get_history(
        rider_id, UserRole.rider
    )

    assert total == 2
    assert len(rides) == 2
    assert all(r.rider_id == rider_id for r in rides)


@pytest.mark.asyncio()
async def test_driver_history_returns_correct_rides(
    repo: FakeRideRepository, settings: Settings
) -> None:
    driver_id = uuid4()
    other_driver = uuid4()
    repo.driver_rides = [
        _ride(uuid4(), driver_id),
        _ride(uuid4(), driver_id),
        _ride(uuid4(), other_driver),
    ]

    rides, total = await RideHistoryService(repo, settings).get_history(
        driver_id, UserRole.driver
    )

    assert total == 2
    assert len(rides) == 2


@pytest.mark.asyncio()
async def test_history_empty_returns_zero_total(
    repo: FakeRideRepository, settings: Settings
) -> None:
    rides, total = await RideHistoryService(repo, settings).get_history(
        uuid4(), UserRole.rider
    )
    assert total == 0
    assert rides == []


@pytest.mark.asyncio()
async def test_pagination_returns_correct_page(
    repo: FakeRideRepository, settings: Settings
) -> None:
    rider_id = uuid4()
    repo.rider_rides = [_ride(rider_id) for _ in range(25)]

    # page 1 — first 10
    rides_p1, total = await RideHistoryService(repo, settings).get_history(
        rider_id, UserRole.rider, page=1, page_size=10
    )
    assert total == 25
    assert len(rides_p1) == 10

    # page 2 — next 10
    rides_p2, _ = await RideHistoryService(repo, settings).get_history(
        rider_id, UserRole.rider, page=2, page_size=10
    )
    assert len(rides_p2) == 10

    # page 3 — remaining 5
    rides_p3, _ = await RideHistoryService(repo, settings).get_history(
        rider_id, UserRole.rider, page=3, page_size=10
    )
    assert len(rides_p3) == 5

    # no overlap between pages
    ids_p1 = {r.id for r in rides_p1}
    ids_p2 = {r.id for r in rides_p2}
    assert ids_p1.isdisjoint(ids_p2)
