"""create inventory and system schemas

Revision ID: 7c67a18f645e
Revises: 
Create Date: 2026-08-11 16:59:14.283900

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c67a18f645e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS inventory")
    op.execute("CREATE SCHEMA IF NOT EXISTS system")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP SCHEMA IF EXISTS inventory CASCADE")
    op.execute("DROP SCHEMA IF EXISTS system CASCADE")
