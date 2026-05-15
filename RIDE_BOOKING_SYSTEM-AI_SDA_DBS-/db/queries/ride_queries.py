from __future__ import annotations

RETURNING_FIELDS = """
  id, rider_id, driver_id, status, origin, destination, ride_type, fare, rating, created_at, updated_at, pickup_latitude, pickup_longitude
"""

INSERT_RIDE = f"""
INSERT INTO rides (id, rider_id, status, origin, destination, ride_type, fare, pickup_latitude, pickup_longitude, created_at, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
RETURNING {RETURNING_FIELDS}
"""

SELECT_RIDE_BY_ID = f"""
SELECT {RETURNING_FIELDS}
FROM rides
WHERE id = $1
"""

SELECT_RIDES_BY_RIDER = f"""
SELECT {RETURNING_FIELDS}
FROM rides
WHERE rider_id = $1
ORDER BY created_at DESC
"""

SELECT_RIDES_BY_DRIVER = f"""
SELECT {RETURNING_FIELDS}
FROM rides
WHERE driver_id = $1
ORDER BY created_at DESC
"""

# For pagination: count total rows before slicing
COUNT_RIDES_BY_RIDER = """
SELECT COUNT(*) FROM rides WHERE rider_id = $1
"""

COUNT_RIDES_BY_DRIVER = """
SELECT COUNT(*) FROM rides WHERE driver_id = $1
"""

# Paginated history queries
SELECT_RIDES_BY_RIDER_PAGINATED = f"""
SELECT {RETURNING_FIELDS}
FROM rides
WHERE rider_id = $1
ORDER BY created_at DESC
LIMIT $2 OFFSET $3
"""

SELECT_RIDES_BY_DRIVER_PAGINATED = f"""
SELECT {RETURNING_FIELDS}
FROM rides
WHERE driver_id = $1
ORDER BY created_at DESC
LIMIT $2 OFFSET $3
"""

SELECT_ACTIVE_RIDE_BY_RIDER = f"""
SELECT {RETURNING_FIELDS}
FROM rides
WHERE rider_id = $1
  AND status IN ('requested', 'offered', 'accepted', 'in_progress')
LIMIT 1
"""

SELECT_ACTIVE_RIDE_BY_DRIVER = f"""
SELECT {RETURNING_FIELDS}
FROM rides
WHERE driver_id = $1
  AND status IN ('offered', 'accepted', 'in_progress')
ORDER BY updated_at DESC
LIMIT 1
"""

# State-guarded status transitions — prevents skipping states at the DB level
START_RIDE = f"""
UPDATE rides
SET status = 'in_progress', updated_at = NOW()
WHERE id = $1
  AND status = 'accepted'
RETURNING {RETURNING_FIELDS}
"""

COMPLETE_RIDE = f"""
UPDATE rides
SET status = 'completed', updated_at = NOW()
WHERE id = $1
  AND status = 'in_progress'
RETURNING {RETURNING_FIELDS}
"""

ASSIGN_DRIVER = f"""
UPDATE rides
SET driver_id = $2, status = 'offered', updated_at = NOW()
WHERE id = $1
  AND status = 'requested'
RETURNING {RETURNING_FIELDS}
"""

ACCEPT_MATCHED_RIDE = f"""
UPDATE rides
SET status = 'accepted', updated_at = NOW()
WHERE id = $1
  AND driver_id = $2
  AND status = 'offered'
RETURNING {RETURNING_FIELDS}
"""

CANCEL_RIDE = f"""
UPDATE rides
SET status = 'cancelled', updated_at = NOW()
WHERE id = $1
  AND status IN ('requested', 'offered', 'accepted')
RETURNING {RETURNING_FIELDS}
"""

UPDATE_DRIVER_RATING = f"""
UPDATE rides
SET rating = $2, updated_at = NOW()
WHERE id = $1
  AND rider_id = $3
  AND status = 'completed'
  AND rating IS NULL
RETURNING {RETURNING_FIELDS}
"""

FIND_AVAILABLE_DRIVER = """
SELECT id
FROM users
WHERE role = 'driver'
  AND id NOT IN (
      SELECT driver_id
      FROM rides
      WHERE status IN ('offered', 'accepted', 'in_progress')
        AND driver_id IS NOT NULL
  )
LIMIT 1
"""

FIND_AVAILABLE_DRIVER_EXCLUDE = """
SELECT id
FROM users
WHERE role = 'driver'
  AND id != $1
  AND id NOT IN (
      SELECT driver_id
      FROM rides
      WHERE status IN ('offered', 'accepted', 'in_progress')
        AND driver_id IS NOT NULL
  )
LIMIT 1
FOR UPDATE SKIP LOCKED
"""

RESET_DRIVER_ASSIGNMENT = f"""
UPDATE rides
SET driver_id = NULL, status = 'requested', updated_at = NOW()
WHERE id = $1
  AND status = 'offered'
  AND driver_id = $2
RETURNING {RETURNING_FIELDS}
"""


# Archive a ride into ride_history then delete from rides (run inside a transaction)
ARCHIVE_RIDE = f"""
INSERT INTO ride_history (id, rider_id, driver_id, status, origin, destination, fare, rating, created_at, updated_at, archived_at)
SELECT id, rider_id, driver_id, status, origin, destination, fare, rating, created_at, updated_at, NOW()
FROM rides
WHERE id = $1
RETURNING id
"""

DELETE_RIDE_BY_ID = """
DELETE FROM rides WHERE id = $1
"""

# Find available drivers for matching - will be ranked in application layer
# $1 = exclude_driver_id (optional), returns all available drivers
FIND_AVAILABLE_DRIVERS_FOR_MATCHING = """
SELECT 
    d.id,
    d.full_name,
    d.email,
    d.rating,
    d.total_rides,
    d.is_available
FROM drivers d
WHERE d.is_available = true
  AND d.id NOT IN (
      SELECT driver_id
      FROM rides
  WHERE status IN ('offered', 'accepted', 'in_progress')
        AND driver_id IS NOT NULL
  )
  AND ($1::uuid IS NULL OR d.id != $1::uuid)
ORDER BY d.rating DESC, d.total_rides DESC
"""

# Get best available driver by ID only (fast lookup for single assignment)
GET_AVAILABLE_DRIVER_BY_ID = """
SELECT id, full_name, email, rating, total_rides
FROM drivers
WHERE id = $1
  AND is_available = true
  AND id NOT IN (
      SELECT driver_id
      FROM rides
      WHERE status IN ('offered', 'accepted', 'in_progress')
        AND driver_id IS NOT NULL
  )
"""
