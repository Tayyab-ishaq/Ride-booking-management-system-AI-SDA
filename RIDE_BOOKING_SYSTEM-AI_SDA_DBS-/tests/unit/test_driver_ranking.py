"""Unit tests for the location-based driver ranking system."""
import pytest
from decimal import Decimal
from uuid import UUID, uuid4
from datetime import datetime, timezone
from math import radians, sin, cos, asin, sqrt

from models.ride import Ride
from core.enums import RideStatus
from services.rides.ranking import (
    DriverRankingService,
    LocalRankingProvider,
    RankedDriver,
)


# Test data
DELHI_LAT, DELHI_LNG = 28.7041, 77.1025
NOIDA_LAT, NOIDA_LNG = 28.5355, 77.3910  # ~20km from Delhi


class TestHaversineDistance:
    """Test haversine distance calculation."""

    def test_distance_same_point(self):
        """Distance between identical points should be 0."""
        distance = DriverRankingService.haversine_distance(
            DELHI_LAT, DELHI_LNG, DELHI_LAT, DELHI_LNG
        )
        assert distance < 0.1  # Allow small floating point error

    def test_distance_known_points(self):
        """Test distance between Delhi and Noida (~34km)."""
        distance = DriverRankingService.haversine_distance(
            DELHI_LAT, DELHI_LNG, NOIDA_LAT, NOIDA_LNG
        )
        # Delhi to Noida is approximately 34km
        assert 32 < distance < 36

    def test_distance_symmetry(self):
        """Distance should be same in both directions."""
        dist1 = DriverRankingService.haversine_distance(
            DELHI_LAT, DELHI_LNG, NOIDA_LAT, NOIDA_LNG
        )
        dist2 = DriverRankingService.haversine_distance(
            NOIDA_LAT, NOIDA_LNG, DELHI_LAT, DELHI_LNG
        )
        assert abs(dist1 - dist2) < 0.01


class TestDriverScoring:
    """Test driver ranking score calculation."""

    def test_score_range(self):
        """Score should be between 0 and 100."""
        score = DriverRankingService.score_driver(
            driver_id=uuid4(),
            full_name="Test Driver",
            email="test@example.com",
            rating=Decimal("4.5"),
            total_rides=50,
            distance_km=2.0,
        )
        assert 0 <= score <= 100

    def test_closer_driver_scores_higher(self):
        """Closer driver should have higher score."""
        score_close = DriverRankingService.score_driver(
            driver_id=uuid4(),
            full_name="Close Driver",
            email="close@example.com",
            rating=Decimal("3.0"),
            total_rides=20,
            distance_km=1.0,
        )
        score_far = DriverRankingService.score_driver(
            driver_id=uuid4(),
            full_name="Far Driver",
            email="far@example.com",
            rating=Decimal("3.0"),
            total_rides=20,
            distance_km=4.0,
        )
        assert score_close > score_far

    def test_higher_rated_driver_scores_higher(self):
        """Higher rated driver should score higher."""
        score_high_rating = DriverRankingService.score_driver(
            driver_id=uuid4(),
            full_name="Good Driver",
            email="good@example.com",
            rating=Decimal("5.0"),
            total_rides=50,
            distance_km=3.0,
        )
        score_low_rating = DriverRankingService.score_driver(
            driver_id=uuid4(),
            full_name="Bad Driver",
            email="bad@example.com",
            rating=Decimal("2.0"),
            total_rides=50,
            distance_km=3.0,
        )
        assert score_high_rating > score_low_rating

    def test_experienced_driver_scores_higher(self):
        """Driver with more rides should score higher."""
        score_exp = DriverRankingService.score_driver(
            driver_id=uuid4(),
            full_name="Experienced",
            email="exp@example.com",
            rating=Decimal("4.0"),
            total_rides=200,
            distance_km=3.0,
        )
        score_new = DriverRankingService.score_driver(
            driver_id=uuid4(),
            full_name="New Driver",
            email="new@example.com",
            rating=Decimal("4.0"),
            total_rides=5,
            distance_km=3.0,
        )
        assert score_exp > score_new


class TestDriverRanking:
    """Test driver ranking functionality."""

    def _create_driver(
        self, name: str, rating: int = 4, rides: int = 50
    ) -> dict:
        """Helper to create driver dict."""
        return {
            "id": uuid4(),
            "full_name": name,
            "email": f"{name.lower().replace(' ', '')}@example.com",
            "rating": rating,
            "total_rides": rides,
        }

    def test_rank_single_driver(self):
        """Ranking single driver should return that driver."""
        driver = self._create_driver("Test Driver")
        ranked = DriverRankingService.rank_drivers(
            [driver], DELHI_LAT, DELHI_LNG
        )
        assert len(ranked) == 1
        assert ranked[0].driver_id == driver["id"]
        assert isinstance(ranked[0], RankedDriver)

    def test_rank_by_distance(self):
        """Drivers should be ranked by distance (closest first)."""
        driver_close = self._create_driver("Close Driver")
        driver_medium = self._create_driver("Medium Driver", rating=4, rides=50)

        # Simulate locations using rank_drivers with mock locations
        drivers = [driver_medium, driver_close]

        # With mock locations, ranking should be by score including distance
        ranked = DriverRankingService.rank_drivers(
            drivers,
            DELHI_LAT,
            DELHI_LNG,
            driver_locations={
                driver_close["id"]: (DELHI_LAT + 0.01, DELHI_LNG),    # ~1km away
                driver_medium["id"]: (DELHI_LAT + 0.04, DELHI_LNG),   # ~4km away
            },
            max_search_radius_km=5.0,
        )

        # Both drivers should be within radius
        assert len(ranked) == 2
        # Closer driver should be ranked higher
        assert ranked[0].driver_id == driver_close["id"]

    def test_rank_filters_outside_radius(self):
        """Drivers outside search radius should be filtered out."""
        driver_close = self._create_driver("Close")
        driver_too_far = self._create_driver("Too Far")

        ranked = DriverRankingService.rank_drivers(
            [driver_close, driver_too_far],
            DELHI_LAT,
            DELHI_LNG,
            driver_locations={
                driver_close["id"]: (DELHI_LAT, DELHI_LNG),           # 0km away
                driver_too_far["id"]: (DELHI_LAT + 1, DELHI_LNG + 1), # ~150km away
            },
            max_search_radius_km=5.0,
        )

        # Only close driver within radius
        assert len(ranked) == 1
        assert ranked[0].driver_id == driver_close["id"]

    def test_rank_multiple_drivers(self):
        """Ranking multiple drivers should return all."""
        drivers = [
            self._create_driver("Driver A", rating=5, rides=100),
            self._create_driver("Driver B", rating=3, rides=20),
            self._create_driver("Driver C", rating=4, rides=50),
        ]
        
        ranked = DriverRankingService.rank_drivers(
            drivers, DELHI_LAT, DELHI_LNG
        )
        
        assert len(ranked) == 3
        # Check order (highest score first)
        assert ranked[0].score >= ranked[1].score >= ranked[2].score


class TestLocalRankingProvider:
    """Test LocalRankingProvider async interface."""

    @pytest.mark.asyncio
    async def test_rank_drivers_with_ride(self):
        """Provider should rank drivers for a ride with location."""
        ride = Ride(
            id=uuid4(),
            rider_id=uuid4(),
            driver_id=None,
            status=RideStatus.requested,
            origin="New Delhi",
            destination="Gurgaon",
            fare=None,
            rating=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            pickup_latitude=Decimal(str(DELHI_LAT)),
            pickup_longitude=Decimal(str(DELHI_LNG)),
        )

        drivers = [
            {
                "id": uuid4(),
                "full_name": "Driver A",
                "email": "a@example.com",
                "rating": 4,
                "total_rides": 50,
            },
            {
                "id": uuid4(),
                "full_name": "Driver B",
                "email": "b@example.com",
                "rating": 5,
                "total_rides": 100,
            },
        ]

        provider = LocalRankingProvider()
        ranked = await provider.rank_drivers(ride, drivers)

        assert len(ranked) == 2
        assert all(isinstance(d, RankedDriver) for d in ranked)
        # Driver B (higher rating, more experience) should be first
        assert ranked[0].driver_id == drivers[1]["id"]

    @pytest.mark.asyncio
    async def test_rank_drivers_missing_coordinates(self):
        """Provider should error if ride missing coordinates."""
        ride = Ride(
            id=uuid4(),
            rider_id=uuid4(),
            driver_id=None,
            status=RideStatus.requested,
            origin="New Delhi",
            destination="Gurgaon",
            fare=None,
            rating=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            pickup_latitude=None,  # Missing!
            pickup_longitude=None,
        )

        provider = LocalRankingProvider()
        
        with pytest.raises(ValueError, match="pickup_latitude and pickup_longitude"):
            await provider.rank_drivers(ride, [])


class TestRankedDriver:
    """Test RankedDriver dataclass."""

    def test_ranked_driver_sorting(self):
        """RankedDriver should support sorting by score."""
        drivers = [
            RankedDriver(
                driver_id=uuid4(),
                full_name="Low Score",
                email="low@example.com",
                rating=Decimal("2"),
                total_rides=10,
                distance_km=5.0,
                score=40.0,
            ),
            RankedDriver(
                driver_id=uuid4(),
                full_name="High Score",
                email="high@example.com",
                rating=Decimal("5"),
                total_rides=200,
                distance_km=2.0,
                score=95.0,
            ),
        ]

        sorted_drivers = sorted(drivers)
        # Should sort by score descending (highest first due to __lt__ implementation)
        assert sorted_drivers[0].score == 95.0
        assert sorted_drivers[1].score == 40.0
