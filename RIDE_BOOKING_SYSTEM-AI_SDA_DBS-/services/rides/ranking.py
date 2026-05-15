"""Driver ranking and matching service for ride assignment."""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from models.ride import Ride


@dataclass(slots=True)
class RankedDriver:
    """Driver with calculated ranking score."""
    driver_id: UUID
    full_name: str
    email: str
    rating: Decimal
    total_rides: int
    distance_km: float
    score: float

    def __lt__(self, other: RankedDriver) -> bool:
        """Enable sorting by score (highest first)."""
        return self.score > other.score


class DriverRankingService:
    """Service for ranking drivers based on multiple criteria.
    
    Scoring factors (pluggable for n8n integration later):
    - Distance (40%): Closer drivers preferred
    - Rating (30%): Higher rated drivers preferred
    - Experience (20%): More completed rides preferred
    - Availability history (10%): Recently accepted drivers preferred
    
    This service is designed to be extended or swapped with external AI ranking
    (e.g., n8n webhook) without changing the matching workflow.
    """

    # Earth radius in kilometers (used for haversine distance calculation)
    EARTH_RADIUS_KM = 6371.0
    
    # Default search radius in kilometers
    DEFAULT_SEARCH_RADIUS_KM = 5.0
    
    # Scoring weights (sum = 1.0)
    WEIGHT_DISTANCE = 0.40
    WEIGHT_RATING = 0.30
    WEIGHT_EXPERIENCE = 0.20
    WEIGHT_AVAILABILITY = 0.10

    @staticmethod
    def haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two points using haversine formula.
        
        Args:
            lat1, lon1: Pickup location (latitude, longitude)
            lat2, lon2: Driver location (latitude, longitude)
            
        Returns:
            Distance in kilometers
        """
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine formula
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        
        return DriverRankingService.EARTH_RADIUS_KM * c

    @classmethod
    def score_driver(
        cls,
        driver_id: UUID,
        full_name: str,
        email: str,
        rating: Decimal,
        total_rides: int,
        distance_km: float,
        max_search_radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
        acceptance_rate: float = 1.0,
    ) -> float:
        """Calculate ranking score for a driver.
        
        Higher score = better match. Score is 0-100.
        
        Args:
            driver_id: Driver UUID
            full_name: Driver name
            email: Driver email
            rating: Driver rating (0-5)
            total_rides: Total completed rides
            distance_km: Distance from pickup location
            max_search_radius_km: Max search radius for normalization
            acceptance_rate: Ratio of accepted to offered rides (0-1)
            
        Returns:
            Score from 0-100
        """
        # Distance score: 0-100, closer = higher
        # Normalize: at max_search_radius_km = 0, at 0km = 100
        distance_score = max(0, 100 - (distance_km / max_search_radius_km * 100))
        
        # Rating score: 0-100, normalized from 0-5
        rating_float = float(rating)
        rating_score = (rating_float / 5.0) * 100
        
        # Experience score: 0-100, normalized logarithmically
        # 1 ride = 50 points, 10 rides = 75 points, 100 rides = 100 points
        if total_rides == 0:
            experience_score = 0
        else:
            # Logarithmic scale: log2(rides + 1) / 7 * 100 (caps at ~100 for 128+ rides)
            experience_score = min(100, (math.log2(total_rides + 1) / 7.0) * 100)
        
        # Availability score: 0-100, based on acceptance rate
        availability_score = acceptance_rate * 100
        
        # Composite score with weights
        score = (
            distance_score * cls.WEIGHT_DISTANCE
            + rating_score * cls.WEIGHT_RATING
            + experience_score * cls.WEIGHT_EXPERIENCE
            + availability_score * cls.WEIGHT_AVAILABILITY
        )
        
        return score

    @classmethod
    def rank_drivers(
        cls,
        drivers: list[dict],
        pickup_latitude: float,
        pickup_longitude: float,
        driver_locations: dict[UUID, tuple[float, float]] | None = None,
        max_search_radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
    ) -> list[RankedDriver]:
        """Rank a list of drivers by score.
        
        Args:
            drivers: List of driver dicts with keys: id, full_name, email, rating, total_rides
            pickup_latitude: Pickup location latitude
            pickup_longitude: Pickup location longitude
            driver_locations: Dict mapping driver_id -> (latitude, longitude).
                            If not provided, drivers are ranked by rating/experience only.
            max_search_radius_km: Max distance to consider driver (km)
            
        Returns:
            List of RankedDriver objects, sorted by score (highest first).
            Drivers outside max_search_radius_km are filtered out.
        """
        ranked = []
        
        for driver in drivers:
            driver_id = driver["id"]
            
            # Get driver location (default to dummy coordinates if not provided)
            if driver_locations and driver_id in driver_locations:
                driver_lat, driver_lon = driver_locations[driver_id]
            else:
                # Without real location data, use default (0, 0) for non-distance-based ranking
                # This allows the service to work even without location tracking
                driver_lat, driver_lon = 0.0, 0.0
            
            # Calculate distance using haversine
            distance = cls.haversine_distance(
                pickup_latitude,
                pickup_longitude,
                driver_lat,
                driver_lon,
            )
            
            # Skip drivers outside search radius
            if distance > max_search_radius_km and driver_locations:
                continue
            
            # Calculate score
            score = cls.score_driver(
                driver_id=driver_id,
                full_name=driver["full_name"],
                email=driver["email"],
                rating=Decimal(str(driver["rating"])),
                total_rides=driver["total_rides"],
                distance_km=distance,
                max_search_radius_km=max_search_radius_km,
                acceptance_rate=1.0,
            )
            
            ranked.append(
                RankedDriver(
                    driver_id=driver_id,
                    full_name=driver["full_name"],
                    email=driver["email"],
                    rating=Decimal(str(driver["rating"])),
                    total_rides=driver["total_rides"],
                    distance_km=distance,
                    score=score,
                )
            )
        
        # Sort by score descending
        ranked.sort()
        return ranked


class RankingProvider:
    """Abstract base for ranking providers (supports n8n webhook injection).
    
    This allows swapping the local ranking algorithm with an external service
    (e.g., n8n AI workflow) without changing the matching service interface.
    """

    async def rank_drivers(
        self,
        ride: Ride,
        available_drivers: list[dict],
    ) -> list[RankedDriver]:
        """Rank available drivers for a ride.
        
        Should be implemented by subclasses (local or external ranking).
        
        Args:
            ride: The Ride object with pickup coordinates
            available_drivers: List of available driver dicts
            
        Returns:
            Ranked list of RankedDriver objects
        """
        raise NotImplementedError


class LocalRankingProvider(RankingProvider):
    """Local ranking implementation using DriverRankingService."""

    def __init__(self, max_search_radius_km: float = DriverRankingService.DEFAULT_SEARCH_RADIUS_KM):
        self.max_search_radius_km = max_search_radius_km

    async def rank_drivers(
        self,
        ride: Ride,
        available_drivers: list[dict],
    ) -> list[RankedDriver]:
        """Rank drivers using local algorithm."""
        if not ride.pickup_latitude or not ride.pickup_longitude:
            raise ValueError("Ride must have pickup_latitude and pickup_longitude for ranking")
        
        return DriverRankingService.rank_drivers(
            drivers=available_drivers,
            pickup_latitude=float(ride.pickup_latitude),
            pickup_longitude=float(ride.pickup_longitude),
            driver_locations=None,  # Location tracking not yet implemented
            max_search_radius_km=self.max_search_radius_km,
        )
