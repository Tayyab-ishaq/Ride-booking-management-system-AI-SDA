from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.config import Settings
from core.enums import RideStatus, RideType
from exception.ride_exceptions import RiderHasActiveRide
from models.ride import Ride
from schemas.rides.create import CreateRideRequest
from services.rides.create import RideCreationService


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _ride(status: RideStatus, rider_id: UUID) -> Ride:
    now = datetime.now(timezone.utc)
    return Ride(
        id=uuid4(),
        rider_id=rider_id,
        driver_id=None,
        status=status,
        origin="A",
        destination="B",
        ride_type=RideType.ridex,
        fare=None,
        rating=None,
        created_at=now,
        updated_at=now,
        pickup_latitude=Decimal("28.6431"),
        pickup_longitude=Decimal("77.2197"),
    )


@dataclass
class FakeRideRepository:
    active_ride: Ride | None = None
    created: list[Ride] = field(default_factory=list)

    async def get_active_ride_by_rider(self, rider_id: UUID) -> Ride | None:
        if self.active_ride and self.active_ride.rider_id == rider_id:
            return self.active_ride
        return None

    async def create(self, ride: Ride) -> Ride:
        persisted = Ride(
            id=ride.id,
            rider_id=ride.rider_id,
            driver_id=ride.driver_id,
            status=ride.status,
            origin=ride.origin,
            destination=ride.destination,
            ride_type=ride.ride_type,
            fare=ride.fare,
            rating=ride.rating,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            pickup_latitude=ride.pickup_latitude,
            pickup_longitude=ride.pickup_longitude,
        )
        self.created.append(persisted)
        return persisted


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
async def test_create_ride_persists_with_requested_status(
    repo: FakeRideRepository, settings: Settings
) -> None:
    rider_id = uuid4()
    payload = CreateRideRequest(
        origin="Home", 
        destination="Office",
        pickup_latitude=28.6431,
        pickup_longitude=77.2197,
    )

    result = await RideCreationService(repo, settings).create_ride(payload, rider_id)

    assert result.status == RideStatus.requested
    assert result.rider_id == rider_id
    assert result.origin == "Home"
    assert result.destination == "Office"
    assert result.driver_id is None
    assert result.fare == Decimal("4.20")
    assert result.pickup_latitude == Decimal("28.6431")
    assert result.pickup_longitude == Decimal("77.2197")
    assert len(repo.created) == 1


@pytest.mark.asyncio()
async def test_create_ride_raises_if_active_ride_exists(
    repo: FakeRideRepository, settings: Settings
) -> None:
    rider_id = uuid4()
    repo.active_ride = _ride(RideStatus.requested, rider_id)
    payload = CreateRideRequest(
        origin="Home", 
        destination="Office",
        pickup_latitude=28.6431,
        pickup_longitude=77.2197,
    )

    with pytest.raises(RiderHasActiveRide):
        await RideCreationService(repo, settings).create_ride(payload, rider_id)


@pytest.mark.asyncio()
async def test_create_ride_allows_different_rider_when_another_has_active(
    repo: FakeRideRepository, settings: Settings
) -> None:
    other_rider = uuid4()
    repo.active_ride = _ride(RideStatus.requested, other_rider)
    my_rider_id = uuid4()
    payload = CreateRideRequest(
        origin="Home", 
        destination="Office",
        pickup_latitude=28.6431,
        pickup_longitude=77.2197,
    )

    result = await RideCreationService(repo, settings).create_ride(payload, my_rider_id)

    assert result.rider_id == my_rider_id


@pytest.mark.asyncio()
async def test_create_ride_uses_estimated_fare_when_provided(
    repo: FakeRideRepository, settings: Settings
) -> None:
    rider_id = uuid4()
    payload = CreateRideRequest(
        origin="Home",
        destination="Office",
        pickup_latitude=28.6431,
        pickup_longitude=77.2197,
        estimated_fare=Decimal("56.00"),
    )

    result = await RideCreationService(repo, settings).create_ride(payload, rider_id)

    assert result.fare == Decimal("56.00")


@pytest.mark.asyncio()
async def test_create_ride_applies_base_fare_floor_when_estimate_is_lower(
    repo: FakeRideRepository, settings: Settings
) -> None:
    rider_id = uuid4()
    payload = CreateRideRequest(
        origin="Home",
        destination="Office",
        pickup_latitude=28.6431,
        pickup_longitude=77.2197,
        estimated_fare=Decimal("1.00"),
    )

    result = await RideCreationService(repo, settings).create_ride(payload, rider_id)

    assert result.fare == Decimal("4.20")
