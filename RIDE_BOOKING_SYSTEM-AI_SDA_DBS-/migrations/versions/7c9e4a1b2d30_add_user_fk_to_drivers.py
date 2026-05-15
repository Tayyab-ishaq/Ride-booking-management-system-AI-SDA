"""add_user_fk_to_drivers

Revision ID: 7c9e4a1b2d30
Revises: 4f2a1c9d7e10
Create Date: 2026-05-09 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7c9e4a1b2d30"
down_revision: Union[str, Sequence[str], None] = "4f2a1c9d7e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For databases created BEFORE removing inheritance: add user_id FK and supporting objects.
    # For NEW databases: user_id and FK are created in b8a2442bbfdb migration, so these are no-ops.
    op.execute("ALTER TABLE drivers ADD COLUMN IF NOT EXISTS user_id UUID;")

    # Backfill existing rows where drivers.id already matches users.id (only if user_id is NULL).
    op.execute("UPDATE drivers SET user_id = id WHERE user_id IS NULL;")

    op.execute("ALTER TABLE drivers ALTER COLUMN user_id SET NOT NULL;")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_drivers_user_id ON drivers (user_id);")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_drivers_user_id_users'
            ) THEN
                ALTER TABLE drivers
                ADD CONSTRAINT fk_drivers_user_id_users
                FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE drivers DROP CONSTRAINT IF EXISTS fk_drivers_user_id_users;")
    op.execute("DROP INDEX IF EXISTS uq_drivers_user_id;")
    op.execute("ALTER TABLE drivers DROP COLUMN IF EXISTS user_id;")
