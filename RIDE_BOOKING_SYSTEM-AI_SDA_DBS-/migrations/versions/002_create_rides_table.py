from typing import Sequence, Union

from alembic import op

# revision identifiers
revision: str = "b2e903f1a847"
down_revision: Union[str, None] = "b7c9e2d4f1a0"   # rides depend on users table
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgcrypto already enabled by migration 001, guard is idempotent
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    op.execute("""
        CREATE TABLE IF NOT EXISTS rides (
            id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            rider_id      UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            driver_id     UUID                  REFERENCES users(id) ON DELETE SET NULL,
            status        VARCHAR(20)  NOT NULL DEFAULT 'requested'
                              CHECK (status IN (
                                  'requested', 'accepted',
                                  'in_progress', 'completed', 'cancelled'
                              )),
            origin        VARCHAR(255) NOT NULL,
            destination   VARCHAR(255) NOT NULL,
            fare          NUMERIC(10, 2),
            rating        SMALLINT     CHECK (rating BETWEEN 1 AND 5),
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_rides_rider_id  ON rides (rider_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rides_driver_id ON rides (driver_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rides_status    ON rides (status);")

    # Partial index — fast lookup of the one active ride per rider
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_rides_active_rider
        ON rides (rider_id)
        WHERE status IN ('requested', 'accepted', 'in_progress');
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS rides;")
