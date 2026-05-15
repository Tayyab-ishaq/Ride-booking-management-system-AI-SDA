from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "006_add_ride_type_and_fare"
down_revision: Union[str, None] = "005_add_offered_ride_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "rides",
        sa.Column("ride_type", sa.String(length=32), nullable=False, server_default="ridex"),
    )

    op.execute(
        """
        UPDATE rides
        SET ride_type = COALESCE(ride_type, 'ridex')
        """
    )

    op.alter_column("rides", "ride_type", server_default=None)


def downgrade() -> None:
    op.drop_column("rides", "ride_type")
