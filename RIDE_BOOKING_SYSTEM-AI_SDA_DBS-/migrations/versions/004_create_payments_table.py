from typing import Sequence, Union

from alembic import op

# revision identifiers
revision: str = "d4e5c6f7a1b2"
down_revision: Union[str, None] = "004_add_offered_ride_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    op.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            ride_id           UUID         NOT NULL UNIQUE REFERENCES rides(id) ON DELETE CASCADE,
            user_id           UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            amount            NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
            status            VARCHAR(25)  NOT NULL DEFAULT 'pending'
                                  CHECK (status IN (
                                      'pending', 'processing', 'completed',
                                      'failed', 'refunded', 'partially_refunded', 'cancelled'
                                  )),
            payment_method    VARCHAR(50)  NOT NULL,
            transaction_id    VARCHAR(255) UNIQUE,
            deleted_at        TIMESTAMPTZ,
            created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments (user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_payments_ride_id ON payments (ride_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments (status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_payments_transaction_id ON payments (transaction_id);")

    # Partial index — fast lookup of incomplete payments
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_active
        ON payments (user_id)
        WHERE status IN ('pending', 'processing');
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS payments;")
