from typing import Sequence, Union

from alembic import op

# revision identifiers
revision: str = "005_add_offered_ride_status"
down_revision: Union[str, None] = "004_pickup_coordinates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE rides
        DROP CONSTRAINT IF EXISTS rides_status_check;
    """)

    op.execute("""
        ALTER TABLE rides
        ADD CONSTRAINT rides_status_check
        CHECK (status IN (
            'requested', 'offered', 'accepted',
            'in_progress', 'completed', 'cancelled'
        ));
    """)

    op.execute("""
        DROP INDEX IF EXISTS idx_rides_active_rider;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_rides_active_rider
        ON rides (rider_id)
        WHERE status IN ('requested', 'offered', 'accepted', 'in_progress');
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE rides
        DROP CONSTRAINT IF EXISTS rides_status_check;
    """)

    op.execute("""
        ALTER TABLE rides
        ADD CONSTRAINT rides_status_check
        CHECK (status IN (
            'requested', 'accepted',
            'in_progress', 'completed', 'cancelled'
        ));
    """)

    op.execute("""
        DROP INDEX IF EXISTS idx_rides_active_rider;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_rides_active_rider
        ON rides (rider_id)
        WHERE status IN ('requested', 'accepted', 'in_progress');
    """)
