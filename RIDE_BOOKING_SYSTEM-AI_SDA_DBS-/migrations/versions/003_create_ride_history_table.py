from typing import Sequence, Union

from alembic import op

# revision identifiers
revision: str = "c3d4b5a6f012"
down_revision: Union[str, None] = "b2e903f1a847"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    op.execute("""
        CREATE TABLE IF NOT EXISTS ride_history (
            id            UUID         PRIMARY KEY,
            rider_id      UUID         NOT NULL,
            driver_id     UUID,
            status        VARCHAR(20)  NOT NULL,
            origin        VARCHAR(255) NOT NULL,
            destination   VARCHAR(255) NOT NULL,
            fare          NUMERIC(10, 2),
            rating        SMALLINT,
            created_at    TIMESTAMPTZ  NOT NULL,
            updated_at    TIMESTAMPTZ  NOT NULL,
            archived_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_ride_history_rider_id ON ride_history (rider_id);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ride_history;")
