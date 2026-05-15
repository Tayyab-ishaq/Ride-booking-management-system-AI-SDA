from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007_merge_006_heads"
down_revision: Union[str, tuple[str, str], None] = (
    "006_add_ride_type_and_fare",
    "006_payment_methods_profiles",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
