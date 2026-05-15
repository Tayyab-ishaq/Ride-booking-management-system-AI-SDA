# Ride Booking Matching System - Implementation Guide

## Overview

This document describes the complete implementation of the location-based ride-to-driver matching workflow according to the activity diagram. The system ranks drivers intelligently and handles rejections with automatic retry logic.

## Architecture & Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ RIDER CREATES RIDE REQUEST                                      │
│ - Sends origin, destination, pickup_latitude, pickup_longitude  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASTAPI BACKEND - RIDE CREATION                                 │
│ - Validates coordinates (lat: ±90°, lng: ±180°)                │
│ - Stores ride with location in database                         │
│ - Status: 'requested'                                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ DRIVER MATCHING TRIGGER (POST /matching/find)                   │
│ 1. Fetch available drivers from database                        │
│ 2. Use DriverRankingService to score each driver                │
│ 3. Sort by score (distance 40%, rating 30%, exp 20%, avail 10%) │
│ 4. Assign top-ranked driver                                    │
│ 5. Store ranked list for rematch on rejection                   │
│ Status: 'accepted' (matched, awaiting final confirmation)       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ DRIVER DECISION                                                 │
│ Driver sees matched ride on dashboard                           │
│ POST /matching/accept  ──→ Confirms acceptance                 │
│         OR                                                      │
│ POST /matching/reject  ──→ Triggers rematch with next driver    │
└─────────────────────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
    ┌───────┐                      ┌──────────────────┐
    │ DONE  │                      │ Next ranked      │
    │ Ride  │                      │ driver assigned  │
    │ ACCEPTED                     │ Loop continues   │
    └───────┘                      └────────┬─────────┘
                                            │
                                    ┌───────▼────────┐
                                    │ If queue empty │
                                    │ Back to        │
                                    │ 'requested'    │
                                    │ New match      │
                                    │ attempt needed │
                                    └────────────────┘
```

## Key Components

### 1. Driver Ranking Service (`services/rides/ranking.py`)

**Purpose**: Score drivers based on multiple factors for intelligent matching.

**Scoring Formula** (0-100 scale):
```
Final Score = 
    Distance Score (0-100) × 0.40    [40% weight - closer is better]
  + Rating Score (0-100)   × 0.30    [30% weight - higher rated better]
  + Experience Score (0-100) × 0.20  [20% weight - more rides better]
  + Availability Score (0-100) × 0.10 [10% weight - acceptance rate]
```

**Key Features**:
- **Haversine Distance Formula**: Calculates great-circle distance between pickup and driver location
- **Pluggable Architecture**: Can swap `LocalRankingProvider` with `WebhookRankingProvider` (n8n) without changing matching logic
- **Distance-aware**: Filters drivers outside configured radius (default 5km)
- **Logarithmic Experience Scaling**: 1 ride = 50pts, 10 rides = 75pts, 128+ rides = 100pts

**Classes**:
- `DriverRankingService`: Static methods for scoring and ranking
- `RankedDriver`: Dataclass holding driver with calculated score
- `RankingProvider`: Abstract base for pluggable ranking
- `LocalRankingProvider`: Concrete implementation using local algorithm

### 2. Ride Model Updates (`models/ride.py`)

Added fields:
```python
pickup_latitude: Decimal | None = None
pickup_longitude: Decimal | None = None
```

### 3. Request Schema (`schemas/rides/create.py`)

Updated `CreateRideRequest`:
```python
pickup_latitude: float = Field(ge=-90, le=90)      # -90 to +90°
pickup_longitude: float = Field(ge=-180, le=180)   # -180 to +180°
```

Validation ensures valid coordinates before database storage.

### 4. Database Migration (`migrations/versions/004_add_pickup_coordinates.py`)

- Adds `pickup_latitude` (NUMERIC 10,8) to rides and ride_history tables
- Adds `pickup_longitude` (NUMERIC 11,8) to rides and ride_history tables
- Creates composite index `idx_rides_pickup_coords` for geospatial queries

### 5. Repository Layer (`repositories/ride_repository.py`)

New methods:
- `get_available_drivers_for_matching(exclude_driver_id)`: Fetches all drivers not in active rides
- `get_driver_by_id(driver_id)`: Gets single driver, checking availability

Updated `create()`: Now saves pickup coordinates to database.

### 6. Matching Service (`services/rides/matching.py`)

**Workflow**:

1. **`find_driver_for_ride(ride_id, rider_id)`**
   - Validate ride and coordinates
   - Fetch available drivers
   - Rank using `ranking_provider`
   - Store ranked list for potential rematch
   - Assign top-ranked driver
   - Returns: Ride with driver assigned, status='accepted'

2. **`driver_accept_matched_ride(ride_id, driver_id)`**
   - Confirm driver acceptance
   - Clean up stored rankings
   - Returns: Ride unchanged, marks as final

3. **`driver_reject_matched_ride(ride_id, driver_id)`** (KEY RETRY LOGIC)
   - Reset current driver assignment
   - If ranked drivers remain: Auto-assign next driver
   - If no drivers left: Return ride to 'requested' for fresh matching
   - Maintains ranked list state machine throughout

4. **`get_matching_status(ride_id, rider_id)`**
   - Polling endpoint for riders to check match status
   - Returns current Ride object

**State Machine**:
```
'requested' 
   ├─→ [find_driver_for_ride] ──→ 'accepted' (driver assigned)
   │
'accepted'
   ├─→ [driver_accept] ──→ 'accepted' (final confirmation)
   ├─→ [driver_reject] ──→ 
   │       ├─→ 'accepted' (next ranked driver assigned)
   │       └─→ 'requested' (no more drivers in queue)
```

## Implementation Details

### Ranking Algorithm Weights

| Factor | Weight | Rationale |
|--------|--------|-----------|
| Distance | 40% | User experience: closest driver = fastest pickup |
| Rating | 30% | Quality: ensures good drivers matched more |
| Experience | 20% | Reliability: experienced drivers handle edge cases |
| Availability | 10% | Consistency: drivers who accept more often |

### Haversine Formula

Calculates geodetic distance between two lat/long points:
```python
a = sin²(Δφ/2) + cos(φ1) × cos(φ2) × sin²(Δλ/2)
c = 2 × atan2(√a, √(1−a))
d = R × c
```
Where R = 6371 km (Earth radius), φ = latitude, λ = longitude

**Accuracy**: ±0.5% for Earth surface distances

### Extension Points for n8n Integration

The system is designed to support n8n later:

1. **Create `WebhookRankingProvider`** in `services/rides/ranking.py`:
   ```python
   class WebhookRankingProvider(RankingProvider):
       async def rank_drivers(self, ride, drivers):
           # POST to n8n webhook
           # Parse n8n AI ranking response
           # Return RankedDriver list
   ```

2. **Update dependency injection** in `api/endpoints/rides/dependencies.py`:
   ```python
   def get_ride_matching_service(...):
       # Use env config to choose provider
       provider = LocalRankingProvider() if USE_LOCAL_RANKING else WebhookRankingProvider()
       return RideMatchingService(repository, settings, provider)
   ```

3. **n8n webhook contract**:
   ```json
   POST /webhook/rank-drivers
   {
     "ride": { "pickup_latitude": 28.7, "pickup_longitude": 77.1 },
     "drivers": [ { "id": "...", "rating": 4.5, ... } ]
   }
   RESPONSE:
   {
     "ranked_drivers": [
       { "id": "...", "score": 85.5 },
       ...
     ]
   }
   ```

## Database Changes

### Migrations to Run

```bash
# In order:
alembic upgrade head  # Runs all pending migrations including 004_add_pickup_coordinates
```

### Tables Modified

**`rides` table**:
- NEW: `pickup_latitude` (NUMERIC 10,8) - nullable
- NEW: `pickup_longitude` (NUMERIC 11,8) - nullable
- NEW INDEX: `idx_rides_pickup_coords` on (pickup_latitude, pickup_longitude)

**`ride_history` table**:
- NEW: `pickup_latitude` (NUMERIC 10,8) - nullable
- NEW: `pickup_longitude` (NUMERIC 11,8) - nullable

## API Changes

### Ride Creation Endpoint

**Request** (POST /rides):
```json
{
  "origin": "New Delhi Station",
  "destination": "T3 Airport",
  "pickup_latitude": 28.6431,
  "pickup_longitude": 77.2197
}
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "rider_id": "...",
  "driver_id": null,
  "status": "requested",
  "origin": "New Delhi Station",
  "destination": "T3 Airport",
  "pickup_latitude": 28.6431,
  "pickup_longitude": 77.2197,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Matching Find Endpoint

**POST /matching/find**
```json
{
  "ride_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response** (Ride with driver assigned):
```json
{
  "...": "same as above",
  "driver_id": "driver-uuid",
  "status": "accepted"
}
```

### Matching Reject Endpoint

**POST /matching/reject**
```json
{
  "ride_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response** (Either next driver or back to requested):
```json
{
  "driver_id": "new-driver-uuid-or-null",
  "status": "accepted-or-requested"
}
```

## Testing

### Unit Tests

File: `tests/unit/test_driver_ranking.py`

Coverage:
- Haversine distance calculation accuracy
- Scoring formula behavior (closer, higher rated, experienced drivers score higher)
- Ranking order validation
- Search radius filtering
- Async ranking provider interface

**Run tests**:
```bash
pytest tests/unit/test_driver_ranking.py -v
```

### Integration Tests

Recommended additions:
1. End-to-end ride creation → driver match → rejection → rematch
2. Multiple rejection scenario exhausting driver queue
3. Polling status endpoint during matching

## Configuration

### Environment Variables

Optional (all have sensible defaults):
```bash
# Ranking algorithm weights
RANKING_WEIGHT_DISTANCE=0.4
RANKING_WEIGHT_RATING=0.3
RANKING_WEIGHT_EXPERIENCE=0.2
RANKING_WEIGHT_AVAILABILITY=0.1

# Search radius
DEFAULT_SEARCH_RADIUS_KM=5.0

# Enable n8n ranking (future)
USE_WEBHOOK_RANKING=false
N8N_WEBHOOK_URL=https://n8n.example.com/webhook/rank-drivers
```

## Performance Considerations

### Database Queries

- `FIND_AVAILABLE_DRIVERS_FOR_MATCHING`: O(d) where d = drivers. Index on `is_available` + NOT IN subquery.
- Composite index on `(pickup_latitude, pickup_longitude)` for future geospatial queries.

### In-Memory State

- `_ride_driver_rankings` dict: Stores ranked driver lists per ride. Auto-cleared when ride accepted or no drivers remain. Max size: active rides × avg_drivers_per_rank.

### Haversine Calculation

- Pure Python math: ~0.5ms per driver
- Can be optimized with PostGIS in future (direct SQL calculation)

## Future Enhancements

1. **Real-time WebSocket Updates**: Instead of polling for match status
2. **Driver Location Tracking**: Store periodic lat/long from mobile app
3. **n8n AI Integration**: Replace local ranking with AI model
4. **Surge Pricing**: Factor into matching decision
5. **Predictive Matching**: Pre-rank drivers before ride request
6. **Rating-based Driver Preferences**: Let riders choose ride type (economy, premium)

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "No nearby drivers" | Distance calc too strict | Increase `DEFAULT_SEARCH_RADIUS_KM` |
| Slow matching | Too many available drivers | Add pagination to driver fetch |
| Inconsistent scores | Float precision | Use Decimal for final storage |
| n8n timeout | Webhook slow | Add timeout handling + fallback to local |

## References

- [Haversine Formula](https://en.wikipedia.org/wiki/Haversine_formula)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- Activity Diagram: `diagram1_ride_booking_driver_assignment.svg`
