from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.config import Settings
from core.enums import RideStatus
from exception.ride_exceptions import (
    InvalidRideTransition,
    RideAlreadyCancelled,
    RideNotFound,
    RideOwnershipError,
)
from models.ride import Ride
from services.rides.lifecycle import RideLifecycleService


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _ride(
    status: RideStatus = RideStatus.requested,
    rider_id: UUID | None = None,
    driver_id: UUID | None = None,
) -> Ride:
    now = datetime.now(timezone.utc)
    return Ride(
        id=uuid4(),
        rider_id=rider_id or uuid4(),
        driver_id=driver_id,
        status=status,
        origin="Downtown",
        destination="Airport",
        fare=None,
        rating=None,
        created_at=now,
        updated_at=now,
    )


def _updated(ride: Ride, **kwargs) -> Ride:
    """Return a new Ride with fields overridden — simulates a DB update."""
    return Ride(
        id=ride.id,
        rider_id=ride.rider_id,
        driver_id=kwargs.get("driver_id", ride.driver_id),
        status=kwargs.get("status", ride.status),
        origin=ride.origin,
        destination=ride.destination,
        fare=ride.fare,
        rating=ride.rating,
        created_at=ride.created_at,
        updated_at=datetime.now(timezone.utc),
    )


# ------------------------------------------------------------------ #
# Fake repository — mirrors RideRepository signatures exactly         #
# ------------------------------------------------------------------ #

@dataclass
class FakeRideRepository:
    rides: dict[UUID, Ride] = field(default_factory=dict)

    async def get_by_id(self, ride_id: UUID) -> Ride | None:
        return self.rides.get(ride_id)

    async def assign_driver(self, ride_id: UUID, driver_id: UUID) -> Ride:
        ride = self.rides.get(ride_id)
        if ride is None or ride.status != RideStatus.requested:
            raise RideNotFound(f"Ride {ride_id} not found or no longer 'requested'")
        updated = _updated(ride, driver_id=driver_id, status=RideStatus.accepted)
        self.rides[ride_id] = updated
        return updated

    async def start_ride(self, ride_id: UUID) -> Ride:
        ride = self.rides.get(ride_id)
        if ride is None or ride.status != RideStatus.accepted:
            raise InvalidRideTransition(f"Ride {ride_id} must be 'accepted' to start")
        updated = _updated(ride, status=RideStatus.in_progress)
        self.rides[ride_id] = updated
        return updated

    async def complete_ride(self, ride_id: UUID) -> Ride:
        ride = self.rides.get(ride_id)
        if ride is None or ride.status != RideStatus.in_progress:
            raise InvalidRideTransition(f"Ride {ride_id} must be 'in_progress' to complete")
        updated = _updated(ride, status=RideStatus.completed)
        self.rides[ride_id] = updated
        return updated

    async def cancel(self, ride_id: UUID) -> Ride:
        ride = self.rides.get(ride_id)
        if ride is None or ride.status not in (RideStatus.requested, RideStatus.accepted):
            raise RideAlreadyCancelled(f"Ride {ride_id} cannot be cancelled")
        updated = _updated(ride, status=RideStatus.cancelled)
        self.rides[ride_id] = updated
        return updated


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
# get_ride                                                             #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio()
async def test_get_ride_returns_ride(repo: FakeRideRepository, settings: Settings) -> None:
    ride = _ride()
    repo.rides[ride.id] = ride
    result = await RideLifecycleService(repo, settings).get_ride(ride.id)
    assert result.id == ride.id


@pytest.mark.asyncio()
async def test_get_ride_raises_not_found(repo: FakeRideRepository, settings: Settings) -> None:
    with pytest.raises(RideNotFound):
        await RideLifecycleService(repo, settings).get_ride(uuid4())


# ------------------------------------------------------------------ #
# accept_ride                                                          #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio()
async def test_accept_ride_assigns_driver(repo: FakeRideRepository, settings: Settings) -> None:
    ride = _ride(RideStatus.requested)
    repo.rides[ride.id] = ride
    driver_id = uuid4()

    result = await RideLifecycleService(repo, settings).accept_ride(ride.id, driver_id)

    assert result.status == RideStatus.accepted
    assert result.driver_id == driver_id


@pytest.mark.asyncio()
async def test_accept_already_accepted_ride_raises(repo: FakeRideRepository, settings: Settings) -> None:
    ride = _ride(RideStatus.accepted, driver_id=uuid4())
    repo.rides[ride.id] = ride

    with pytest.raises(RideNotFound):
        await RideLifecycleService(repo, settings).accept_ride(ride.id, uuid4())


# ------------------------------------------------------------------ #
# start_ride — ownership + transition guard                           #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio()
async def test_start_ride_sets_in_progress(repo: FakeRideRepository, settings: Settings) -> None:
    driver_id = uuid4()
    ride = _ride(RideStatus.accepted, driver_id=driver_id)
    repo.rides[ride.id] = ride

    result = await RideLifecycleService(repo, settings).start_ride(ride.id, driver_id)

    assert result.status == RideStatus.in_progress


@pytest.mark.asyncio()
async def test_start_ride_rejects_wrong_driver(repo: FakeRideRepository, settings: Settings) -> None:
    ride = _ride(RideStatus.accepted, driver_id=uuid4())
    repo.rides[ride.id] = ride

    with pytest.raises(RideOwnershipError):
        await RideLifecycleService(repo, settings).start_ride(ride.id, uuid4())


@pytest.mark.asyncio()
async def test_start_ride_rejects_wrong_status(repo: FakeRideRepository, settings: Settings) -> None:
    driver_id = uuid4()
    ride = _ride(RideStatus.requested, driver_id=driver_id)
    repo.rides[ride.id] = ride

    # ownership passes but DB guard rejects wrong status
    with pytest.raises(InvalidRideTransition):
        await RideLifecycleService(repo, settings).start_ride(ride.id, driver_id)


# ------------------------------------------------------------------ #
# complete_ride — ownership + transition guard                        #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio()
async def test_complete_ride_sets_completed(repo: FakeRideRepository, settings: Settings) -> None:
    driver_id = uuid4()
    ride = _ride(RideStatus.in_progress, driver_id=driver_id)
    repo.rides[ride.id] = ride

    result = await RideLifecycleService(repo, settings).complete_ride(ride.id, driver_id)

    assert result.status == RideStatus.completed


@pytest.mark.asyncio()
async def test_complete_ride_rejects_wrong_driver(repo: FakeRideRepository, settings: Settings) -> None:
    ride = _ride(RideStatus.in_progress, driver_id=uuid4())
    repo.rides[ride.id] = ride

    with pytest.raises(RideOwnershipError):
        await RideLifecycleService(repo, settings).complete_ride(ride.id, uuid4())


@pytest.mark.asyncio()
async def test_complete_ride_rejects_wrong_status(repo: FakeRideRepository, settings: Settings) -> None:
    driver_id = uuid4()
    ride = _ride(RideStatus.accepted, driver_id=driver_id)
    repo.rides[ride.id] = ride

    with pytest.raises(InvalidRideTransition):
        await RideLifecycleService(repo, settings).complete_ride(ride.id, driver_id)


# ------------------------------------------------------------------ #
# cancel_ride                                                          #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio()
async def test_cancel_requested_ride(repo: FakeRideRepository, settings: Settings) -> None:
    ride = _ride(RideStatus.requested)
    repo.rides[ride.id] = ride
    result = await RideLifecycleService(repo, settings).cancel_ride(ride.id)
    assert result.status == RideStatus.cancelled


@pytest.mark.asyncio()
async def test_cancel_accepted_ride(repo: FakeRideRepository, settings: Settings) -> None:
    ride = _ride(RideStatus.accepted, driver_id=uuid4())
    repo.rides[ride.id] = ride
    result = await RideLifecycleService(repo, settings).cancel_ride(ride.id)
    assert result.status == RideStatus.cancelled


@pytest.mark.asyncio()
async def test_cancel_in_progress_raises(repo: FakeRideRepository, settings: Settings) -> None:
    ride = _ride(RideStatus.in_progress, driver_id=uuid4())
    repo.rides[ride.id] = ride
    with pytest.raises(RideAlreadyCancelled):
        await RideLifecycleService(repo, settings).cancel_ride(ride.id)


@pytest.mark.asyncio()
async def test_cancel_completed_raises(repo: FakeRideRepository, settings: Settings) -> None:
    ride = _ride(RideStatus.completed, driver_id=uuid4())
    repo.rides[ride.id] = ride
    with pytest.raises(RideAlreadyCancelled):
        await RideLifecycleService(repo, settings).cancel_ride(ride.id)


@pytest.mark.asyncio()
async def test_cancel_nonexistent_raises(repo: FakeRideRepository, settings: Settings) -> None:
    with pytest.raises(RideAlreadyCancelled):
        await RideLifecycleService(repo, settings).cancel_ride(uuid4())
