from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_payment_methods_profiles"
down_revision: Union[str, None] = "d4e5c6f7a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_role_check;
        """
    )
    op.execute(
        """
        ALTER TABLE users
        ADD CONSTRAINT users_role_check
        CHECK (role IN ('rider', 'driver', 'admin'));
        """
    )

    op.execute(
        """
        ALTER TABLE drivers
        ADD COLUMN IF NOT EXISTS total_earnings NUMERIC(12, 2) NOT NULL DEFAULT 0.00;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_methods (
            id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id      UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            method_type  VARCHAR(20)  NOT NULL CHECK (method_type IN ('card', 'wallet', 'cash')),
            token_ref    VARCHAR(255) NOT NULL,
            is_default   BOOLEAN      NOT NULL DEFAULT false,
            created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_methods_user_token
        ON payment_methods (user_id, token_ref);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_payment_methods_user_id
        ON payment_methods (user_id);
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rider_profiles (
            user_id                   UUID         PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            phone_number              VARCHAR(40),
            emergency_contact_name    VARCHAR(120),
            emergency_contact_phone   VARCHAR(40),
            payment_method            VARCHAR(20)  NOT NULL DEFAULT 'card',
            wallet_balance            NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
            is_verified               BOOLEAN      NOT NULL DEFAULT false,
            total_rides               INTEGER      NOT NULL DEFAULT 0,
            average_rating            NUMERIC(3, 2) NOT NULL DEFAULT 0.00,
            created_at                TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at                TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        """
        INSERT INTO rider_profiles (user_id)
        SELECT id
        FROM users
        WHERE role = 'rider'
        ON CONFLICT (user_id) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS rider_profiles;")
    op.execute("DROP TABLE IF EXISTS payment_methods;")
    op.execute("ALTER TABLE drivers DROP COLUMN IF EXISTS total_earnings;")

    op.execute(
        """
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_role_check;
        """
    )
    op.execute(
        """
        ALTER TABLE users
        ADD CONSTRAINT users_role_check
        CHECK (role IN ('rider', 'driver'));
        """
    )
