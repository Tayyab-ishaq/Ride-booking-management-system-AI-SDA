"""create_driver_table

Revision ID: b8a2442bbfdb
Revises: c3d4b5a6f012
Create Date: 2026-05-08 20:56:13.504386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8a2442bbfdb'
down_revision: Union[str, Sequence[str], None] = 'c3d4b5a6f012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


"""create_driver_table

Revision ID: b8a2442bbfdb
Revises: c3d4b5a6f012
Create Date: 2026-05-08 20:56:13.504386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8a2442bbfdb'
down_revision: Union[str, Sequence[str], None] = 'c3d4b5a6f012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE TABLE drivers (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL UNIQUE,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            license_number VARCHAR(50) NOT NULL,
            vehicle_number VARCHAR(50) NOT NULL,
            vehicle_type VARCHAR(50) NOT NULL,
            rating DECIMAL(3,2) DEFAULT 0.00,
            total_rides INTEGER DEFAULT 0,
            is_available BOOLEAN DEFAULT true,
            CONSTRAINT fk_drivers_user_id_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_drivers_license_number ON drivers (license_number);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_drivers_vehicle_number ON drivers (vehicle_number);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_drivers_available ON drivers (is_available);")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS drivers;")

