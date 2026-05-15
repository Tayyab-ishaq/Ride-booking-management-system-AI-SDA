from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "004_pickup_coordinates"
down_revision: Union[str, None] = "7c9e4a1b2d30"  # depends on latest migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pickup_latitude and pickup_longitude to rides and ride_history tables."""
    # Add columns to rides table
    op.add_column(
        "rides",
        sa.Column("pickup_latitude", sa.Numeric(10, 8), nullable=True),
    )
    op.add_column(
        "rides",
        sa.Column("pickup_longitude", sa.Numeric(11, 8), nullable=True),
    )

    # Add columns to ride_history table
    op.add_column(
        "ride_history",
        sa.Column("pickup_latitude", sa.Numeric(10, 8), nullable=True),
    )
    op.add_column(
        "ride_history",
        sa.Column("pickup_longitude", sa.Numeric(11, 8), nullable=True),
    )

    # Create index for geospatial queries (latitude is more selective)
    op.create_index(
        "idx_rides_pickup_coords",
        "rides",
        ["pickup_latitude", "pickup_longitude"],
        unique=False,
    )


def downgrade() -> None:
    """Remove pickup coordinates from rides and ride_history tables."""
    op.drop_index("idx_rides_pickup_coords", table_name="rides")
    op.drop_column("rides", "pickup_longitude")
    op.drop_column("rides", "pickup_latitude")
    op.drop_column("ride_history", "pickup_longitude")
    op.drop_column("ride_history", "pickup_latitude")
