from __future__ import annotations

# Driver table queries - drivers now reference users via user_id
INSERT_DRIVER = """
INSERT INTO drivers (
	id,
	user_id,
	full_name,
	email,
	password_hash,
	role,
	created_at,
	updated_at,
	license_number,
	vehicle_number,
	vehicle_type,
	rating,
	total_rides,
	is_available
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
RETURNING id
"""

# Return a joined driver+user view
SELECT_DRIVER_BY_ID = """
SELECT
	users.id,
	users.full_name,
	users.email,
	users.password_hash,
	users.role,
	users.created_at,
	users.updated_at,
	drivers.license_number,
	drivers.vehicle_number,
	drivers.vehicle_type,
	drivers.rating,
	drivers.total_rides,
	drivers.is_available
FROM drivers
JOIN users ON users.id = drivers.user_id
WHERE drivers.id = $1
"""

SELECT_DRIVER_BY_EMAIL = """
SELECT
	users.id,
	users.full_name,
	users.email,
	users.password_hash,
	users.role,
	users.created_at,
	users.updated_at,
	drivers.license_number,
	drivers.vehicle_number,
	drivers.vehicle_type,
	drivers.rating,
	drivers.total_rides,
	drivers.is_available
FROM drivers
JOIN users ON users.id = drivers.user_id
WHERE users.email = $1
"""

SELECT_AVAILABLE_DRIVERS = """
SELECT
	users.id,
	users.full_name,
	users.email,
	users.password_hash,
	users.role,
	users.created_at,
	users.updated_at,
	drivers.license_number,
	drivers.vehicle_number,
	drivers.vehicle_type,
	drivers.rating,
	drivers.total_rides,
	drivers.is_available
FROM drivers
JOIN users ON users.id = drivers.user_id
WHERE drivers.is_available = true
ORDER BY drivers.rating DESC, drivers.total_rides DESC
"""

UPDATE_DRIVER_AVAILABILITY = """
UPDATE drivers
SET is_available = $2, updated_at = NOW()
WHERE id = $1 OR user_id = $1
RETURNING id
"""

UPDATE_DRIVER_RATING = """
UPDATE drivers
SET rating = $2, total_rides = total_rides + 1, updated_at = NOW()
WHERE id = $1
RETURNING id
"""

# Vehicles
INSERT_VEHICLE = """
INSERT INTO vehicles (vehicle_id, plate_no, driver_id, make_model, color, vehicle_type, created_at, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
RETURNING vehicle_id
"""

SELECT_NEARBY_DRIVERS = """
WITH latest_locations AS (
    SELECT DISTINCT ON (dl.driver_id)
        dl.driver_id,
        dl.latitude,
        dl.longitude,
        dl.recorded_at
    FROM driver_locations dl
    ORDER BY dl.driver_id, dl.recorded_at DESC
),
available AS (
    SELECT
        d.id AS driver_id,
        d.user_id,
        ll.latitude,
        ll.longitude
    FROM drivers d
    JOIN latest_locations ll ON ll.driver_id = d.id
    WHERE d.is_available = true
)
SELECT
    a.driver_id,
    u.full_name,
    a.latitude,
    a.longitude,
    (
        6371 * acos(
            LEAST(
                1,
                cos(radians($1)) * cos(radians(a.latitude::float8))
                * cos(radians(a.longitude::float8) - radians($2))
                + sin(radians($1)) * sin(radians(a.latitude::float8))
            )
        )
    ) AS distance_km
FROM available a
JOIN users u ON u.id = a.user_id
WHERE (
    6371 * acos(
        LEAST(
            1,
            cos(radians($1)) * cos(radians(a.latitude::float8))
            * cos(radians(a.longitude::float8) - radians($2))
            + sin(radians($1)) * sin(radians(a.latitude::float8))
        )
    )
) <= $3
ORDER BY distance_km ASC
LIMIT 100
"""

SELECT_DRIVER_EARNINGS_SUMMARY = """
SELECT
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_rides,
    COALESCE(SUM(fare) FILTER (WHERE status = 'completed'), 0) AS total_earnings,
    COALESCE(AVG(fare) FILTER (WHERE status = 'completed'), 0) AS average_fare
FROM rides
WHERE driver_id = $1
  AND ($2::timestamptz IS NULL OR updated_at >= $2::timestamptz)
  AND ($3::timestamptz IS NULL OR updated_at <= $3::timestamptz)
"""
