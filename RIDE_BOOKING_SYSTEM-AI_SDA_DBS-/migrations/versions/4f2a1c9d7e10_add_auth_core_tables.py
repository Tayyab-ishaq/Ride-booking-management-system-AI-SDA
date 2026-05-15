"""drop_rider_and_add_auth_core_tables

Revision ID: 4f2a1c9d7e10
Revises: b8a2442bbfdb
Create Date: 2026-05-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4f2a1c9d7e10"
down_revision: Union[str, Sequence[str], None] = "b8a2442bbfdb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    # Auth layer tables in ERD.
    op.execute("""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token_id      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id       UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            access_token  TEXT         NOT NULL,
            refresh_token TEXT         NOT NULL,
            expires_at    TIMESTAMPTZ  NOT NULL,
            is_revoked    BOOLEAN      NOT NULL DEFAULT false,
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id ON auth_tokens (user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires_at ON auth_tokens (expires_at);")

    op.execute("""
        CREATE TABLE IF NOT EXISTS otps (
            otp_id       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id      UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            code         VARCHAR(12)  NOT NULL,
            expires_at   TIMESTAMPTZ  NOT NULL,
            created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_otps_user_id ON otps (user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_otps_expires_at ON otps (expires_at);")

    # Core entities in ERD (up to driver section).
    op.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            vehicle_id    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            plate_no      VARCHAR(20)  NOT NULL UNIQUE,
            driver_id     UUID         NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
            make_model    VARCHAR(120) NOT NULL,
            color         VARCHAR(40),
            vehicle_type  VARCHAR(50)  NOT NULL,
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_driver_id ON vehicles (driver_id);")

    op.execute("""
        CREATE TABLE IF NOT EXISTS driver_locations (
            loc_id       UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
            driver_id    UUID          NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
            latitude     NUMERIC(9, 6) NOT NULL,
            longitude    NUMERIC(9, 6) NOT NULL,
            recorded_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_driver_locations_driver_id ON driver_locations (driver_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_driver_locations_recorded_at ON driver_locations (recorded_at);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS driver_locations;")
    op.execute("DROP TABLE IF EXISTS vehicles;")
    op.execute("DROP TABLE IF EXISTS otps;")
    op.execute("DROP TABLE IF EXISTS auth_tokens;")
