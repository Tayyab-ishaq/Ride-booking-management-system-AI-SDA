SELECT_USER_BY_EMAIL = """
SELECT id, full_name, email, password_hash, role, created_at, updated_at
FROM users
WHERE email = $1
"""

INSERT_USER = """
INSERT INTO users (id, full_name, email, password_hash, role, created_at, updated_at)
VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
RETURNING id, full_name, email, password_hash, role, created_at, updated_at
"""

SELECT_USER_BY_ID = "SELECT * FROM users WHERE id = $1"

INSERT_RIDER_PROFILE_IF_MISSING = """
INSERT INTO rider_profiles (
    user_id,
    payment_method,
    wallet_balance,
    is_verified,
    total_rides,
    average_rating,
    created_at,
    updated_at
)
VALUES ($1, 'card', 0.00, false, 0, 0.00, NOW(), NOW())
ON CONFLICT (user_id) DO NOTHING
RETURNING user_id
"""
