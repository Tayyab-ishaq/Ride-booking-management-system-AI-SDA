from __future__ import annotations

# ================================================================ #
# Create                                                           #
# ================================================================ #

INSERT_PAYMENT = """
    INSERT INTO payments (id, ride_id, user_id, amount, status, payment_method, transaction_id, created_at, updated_at)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    RETURNING *;
"""

# ================================================================ #
# Read                                                              #
# ================================================================ #

SELECT_PAYMENT_BY_ID = """
    SELECT * FROM payments WHERE id = $1;
"""

SELECT_PAYMENT_BY_RIDE_ID = """
    SELECT * FROM payments WHERE ride_id = $1;
"""

SELECT_PAYMENTS_BY_USER_ID = """
    SELECT * FROM payments WHERE user_id = $1;
"""

SELECT_PAYMENT_BY_TRANSACTION_ID = """
    SELECT * FROM payments WHERE transaction_id = $1;
"""

SELECT_PAYMENTS_BY_USER_PAGINATED = """
    SELECT * FROM payments 
    WHERE user_id = $1
    ORDER BY created_at DESC
    LIMIT $2 OFFSET $3;
"""

COUNT_PAYMENTS_BY_USER = """
    SELECT COUNT(*) FROM payments WHERE user_id = $1;
"""

# ================================================================ #
# Update                                                            #
# ================================================================ #

UPDATE_PAYMENT_STATUS = """
    UPDATE payments 
    SET status = $1, updated_at = $2 
    WHERE id = $3
    RETURNING *;
"""

UPDATE_PAYMENT_TRANSACTION_ID = """
    UPDATE payments 
    SET transaction_id = $1, updated_at = $2 
    WHERE id = $3
    RETURNING *;
"""

# ================================================================ #
# Delete                                                            #
# ================================================================ #

DELETE_PAYMENT_BY_ID = """
    DELETE FROM payments WHERE id = $1;
"""

ARCHIVE_PAYMENT = """
    UPDATE payments 
    SET deleted_at = $1
    WHERE id = $2;
"""

# ================================================================ #
# Payment methods                                                   #
# ================================================================ #

INSERT_PAYMENT_METHOD = """
    INSERT INTO payment_methods (id, user_id, method_type, token_ref, is_default, created_at, updated_at)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    RETURNING *;
"""

SELECT_PAYMENT_METHOD_BY_ID = """
    SELECT * FROM payment_methods WHERE id = $1;
"""

SELECT_PAYMENT_METHODS_BY_USER_ID = """
    SELECT * FROM payment_methods
    WHERE user_id = $1
    ORDER BY is_default DESC, created_at DESC;
"""

SET_DEFAULT_PAYMENT_METHOD = """
    UPDATE payment_methods
    SET is_default = CASE WHEN id = $2 THEN true ELSE false END,
        updated_at = NOW()
    WHERE user_id = $1;
"""

DELETE_PAYMENT_METHOD_BY_ID = """
    DELETE FROM payment_methods
    WHERE id = $1 AND user_id = $2;
"""
