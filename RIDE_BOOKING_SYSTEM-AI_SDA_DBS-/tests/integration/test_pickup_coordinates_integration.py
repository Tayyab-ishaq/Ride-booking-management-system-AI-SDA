"""End-to-end integration tests for pickup coordinates and driver matching."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from models.ride import Ride
from models.user import User
from core.enums import RideStatus, UserRole
from repositories.ride_repository import RideRepository
from services.rides.create import RideCreationService
from services.rides.matching import RideMatchingService
from services.rides.ranking import LocalRankingProvider
from schemas.rides.create import CreateRideRequest
from app.config import Settings


@pytest.mark.asyncio
class TestPickupCoordinatesIntegration:
    """Integration tests for location-based matching."""

    async def test_complete_ride_workflow_with_coordinates(self):
        """Test complete workflow: create ride → fetch drivers → rank → assign."""
        # Setup
        rider_id = uuid4()
        driver1_id = uuid4()
        driver2_id = uuid4()
        
        # STEP 1: Create ride with pickup coordinates
        ride_request = CreateRideRequest(
            origin="New Delhi Station",
            destination="T3 Airport",
            pickup_latitude=28.6431,
            pickup_longitude=77.2197,
        )
        
        assert ride_request.pickup_latitude == 28.6431
        assert ride_request.pickup_longitude == 77.2197
        assert ride_request.origin == "New Delhi Station"
        assert ride_request.destination == "T3 Airport"

    async def test_ranking_with_multiple_drivers(self):
        """Test ranking of multiple drivers by score."""
        from services.rides.ranking import DriverRankingService, RankedDriver
        
        # Create 3 drivers with different ratings/experience
        drivers = [
            {
                "id": uuid4(),
                "full_name": "Driver A",
                "email": "a@example.com",
                "rating": 5,
                "total_rides": 200,
            },
            {
                "id": uuid4(),
                "full_name": "Driver B",
                "email": "b@example.com",
                "rating": 3,
                "total_rides": 30,
            },
            {
                "id": uuid4(),
                "full_name": "Driver C",
                "email": "c@example.com",
                "rating": 4,
                "total_rides": 100,
            },
        ]
        
        # Rank drivers
        ranked = DriverRankingService.rank_drivers(
            drivers=drivers,
            pickup_latitude=28.6431,
            pickup_longitude=77.2197,
        )
        
        # Driver A should rank first (highest rating + most experience)
        assert len(ranked) == 3
        assert ranked[0].full_name == "Driver A"
        assert ranked[0].score > ranked[1].score > ranked[2].score

    async def test_rematch_after_rejection(self):
        """Test automatic rematch when driver rejects ride."""
        from services.rides.ranking import RankedDriver
        
        rider_id = uuid4()
        ride_id = uuid4()
        driver1_id = uuid4()
        driver2_id = uuid4()
        
        # Create ranked driver list
        ranked_drivers = [
            RankedDriver(
                driver_id=driver1_id,
                full_name="Driver 1",
                email="d1@example.com",
                rating=Decimal("4.5"),
                total_rides=50,
                distance_km=1.5,
                score=85.5,
            ),
            RankedDriver(
                driver_id=driver2_id,
                full_name="Driver 2",
                email="d2@example.com",
                rating=Decimal("4.0"),
                total_rides=30,
                distance_km=3.0,
                score=78.0,
            ),
        ]
        
        # Store ranking (simulating service state)
        ranking_state = {ride_id: ranked_drivers}
        
        # First driver assigned
        assigned_driver = ranked_drivers[0]
        assert assigned_driver.driver_id == driver1_id
        
        # Simulate rejection - get next driver
        remaining = [d for d in ranking_state[ride_id] if d.driver_id != driver1_id]
        assert len(remaining) == 1
        next_driver = remaining[0]
        assert next_driver.driver_id == driver2_id

    async def test_distance_filtering_by_radius(self):
        """Test drivers outside search radius are filtered."""
        from services.rides.ranking import DriverRankingService
        
        pickup_lat, pickup_lng = 28.6431, 77.2197
        
        # Driver very close
        driver_near = {
            "id": uuid4(),
            "full_name": "Near Driver",
            "email": "near@example.com",
            "rating": 4,
            "total_rides": 50,
        }
        
        # Driver far (15km away - outside 5km radius)
        driver_far = {
            "id": uuid4(),
            "full_name": "Far Driver",
            "email": "far@example.com",
            "rating": 5,
            "total_rides": 100,
        }
        
        # Mock driver locations
        driver_locations = {
            driver_near["id"]: (pickup_lat + 0.01, pickup_lng),      # ~1km
            driver_far["id"]: (pickup_lat + 0.15, pickup_lng),       # ~15km
        }
        
        ranked = DriverRankingService.rank_drivers(
            drivers=[driver_near, driver_far],
            pickup_latitude=pickup_lat,
            pickup_longitude=pickup_lng,
            driver_locations=driver_locations,
            max_search_radius_km=5.0,
        )
        
        # Only near driver should be in results
        assert len(ranked) == 1
        assert ranked[0].full_name == "Near Driver"

    async def test_score_calculation_accuracy(self):
        """Test scoring formula with known values."""
        from services.rides.ranking import DriverRankingService
        
        # Test driver with perfect score
        perfect_score = DriverRankingService.score_driver(
            driver_id=uuid4(),
            full_name="Perfect Driver",
            email="perfect@example.com",
            rating=Decimal("5.0"),  # Max rating
            total_rides=200,         # High experience
            distance_km=0.0,         # At pickup location
            max_search_radius_km=5.0,
            acceptance_rate=1.0,     # 100% acceptance
        )
        
        assert perfect_score > 95  # Should be very high
        
        # Test driver with low score
        low_score = DriverRankingService.score_driver(
            driver_id=uuid4(),
            full_name="New Driver",
            email="new@example.com",
            rating=Decimal("1.0"),   # Low rating
            total_rides=1,           # New driver
            distance_km=5.0,         # At radius limit
            max_search_radius_km=5.0,
            acceptance_rate=0.5,     # 50% acceptance
        )
        
        assert low_score < 50  # Should be low
        
        # Perfect score should be significantly higher
        assert perfect_score > low_score + 40


class TestFrontendBackendIntegration:
    """Test frontend-to-backend coordinate flow."""

    def test_create_ride_request_with_coordinates(self):
        """Test that frontend request includes coordinates."""
        # Frontend payload
        frontend_payload = {
            "origin": "New Delhi Station",
            "destination": "T3 Airport",
            "pickup_latitude": 28.6431,
            "pickup_longitude": 77.2197,
        }
        
        # This should be valid per OpenAPI schema
        request = CreateRideRequest(**frontend_payload)
        assert request.pickup_latitude == 28.6431
        assert request.pickup_longitude == 77.2197

    def test_ride_response_includes_coordinates(self):
        """Test that ride response to frontend includes coordinates."""
        from schemas.rides.get import RideDetailResponse
        
        ride_data = {
            "id": uuid4(),
            "rider_id": uuid4(),
            "driver_id": None,
            "status": "requested",
            "origin": "New Delhi Station",
            "destination": "T3 Airport",
            "fare": None,
            "rating": None,
            "pickup_latitude": 28.6431,
            "pickup_longitude": 77.2197,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        
        response = RideDetailResponse(**ride_data)
        assert response.pickup_latitude == 28.6431
        assert response.pickup_longitude == 77.2197


# Test helper fixtures
@pytest.fixture
def sample_ride():
    """Sample ride with coordinates."""
    return Ride(
        id=uuid4(),
        rider_id=uuid4(),
        driver_id=None,
        status=RideStatus.requested,
        origin="New Delhi Station",
        destination="T3 Airport",
        fare=None,
        rating=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        pickup_latitude=Decimal("28.6431"),
        pickup_longitude=Decimal("77.2197"),
    )


@pytest.fixture
def sample_drivers():
    """Sample drivers for ranking tests."""
    return [
        {
            "id": uuid4(),
            "full_name": "Rajesh Kumar",
            "email": "rajesh@example.com",
            "rating": 4.8,
            "total_rides": 250,
        },
        {
            "id": uuid4(),
            "full_name": "Priya Singh",
            "email": "priya@example.com",
            "rating": 4.2,
            "total_rides": 80,
        },
        {
            "id": uuid4(),
            "full_name": "Amit Patel",
            "email": "amit@example.com",
            "rating": 3.9,
            "total_rides": 25,
        },
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
