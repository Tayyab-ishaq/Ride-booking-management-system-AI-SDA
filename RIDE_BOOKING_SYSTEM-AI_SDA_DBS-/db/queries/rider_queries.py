from __future__ import annotations

# Rider table queries
INSERT_RIDER = """
INSERT INTO riders (id, full_name, email, password_hash, role, created_at, updated_at, phone_number, emergency_contact_name, emergency_contact_phone, payment_method, wallet_balance, is_verified, total_rides, average_rating)
VALUES ($1, $2, $3, $4, $5, NOW(), NOW(), $6, $7, $8, $9, $10, $11, $12, $13)
RETURNING id, full_name, email, password_hash, role, created_at, updated_at, phone_number, emergency_contact_name, emergency_contact_phone, payment_method, wallet_balance, is_verified, total_rides, average_rating
"""

SELECT_RIDER_BY_ID = """
SELECT id, full_name, email, password_hash, role, created_at, updated_at, phone_number, emergency_contact_name, emergency_contact_phone, payment_method, wallet_balance, is_verified, total_rides, average_rating
FROM riders
WHERE id = $1
"""

SELECT_RIDER_BY_EMAIL = """
SELECT id, full_name, email, password_hash, role, created_at, updated_at, phone_number, emergency_contact_name, emergency_contact_phone, payment_method, wallet_balance, is_verified, total_rides, average_rating
FROM riders
WHERE email = $1
"""

SELECT_VERIFIED_RIDERS = """
SELECT id, full_name, email, password_hash, role, created_at, updated_at, phone_number, emergency_contact_name, emergency_contact_phone, payment_method, wallet_balance, is_verified, total_rides, average_rating
FROM riders
WHERE is_verified = true
ORDER BY created_at DESC
"""

UPDATE_RIDER_VERIFICATION = """
UPDATE riders
SET is_verified = $2, updated_at = NOW()
WHERE id = $1
RETURNING id, full_name, email, password_hash, role, created_at, updated_at, phone_number, emergency_contact_name, emergency_contact_phone, payment_method, wallet_balance, is_verified, total_rides, average_rating
"""

UPDATE_RIDER_WALLET = """
UPDATE riders
SET wallet_balance = $2, updated_at = NOW()
WHERE id = $1
RETURNING id, full_name, email, password_hash, role, created_at, updated_at, phone_number, emergency_contact_name, emergency_contact_phone, payment_method, wallet_balance, is_verified, total_rides, average_rating
"""

UPDATE_RIDER_RATING = """
UPDATE riders
SET average_rating = $2, total_rides = total_rides + 1, updated_at = NOW()
WHERE id = $1
RETURNING id, full_name, email, password_hash, role, created_at, updated_at, phone_number, emergency_contact_name, emergency_contact_phone, payment_method, wallet_balance, is_verified, total_rides, average_rating
"""
