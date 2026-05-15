from typing import Sequence, Union

# NOTE:
# This revision is retained as a compatibility bridge because earlier history
# used it as an "offered status" migration head. The effective status change
# now lives in revision `005_add_offered_ride_status`.

# revision identifiers
revision: str = "004_add_offered_ride_status"
down_revision: Union[str, None] = "005_add_offered_ride_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op compatibility migration.
    pass


def downgrade() -> None:
    # No-op compatibility migration.
    pass
