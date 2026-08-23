"""rename_id_to_pricelist_id_in_item_pricelist

Revision ID: 63b865b5ada5
Revises: 5c9ca3d9408d
Create Date: 2026-08-23 14:18:48.582297

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63b865b5ada5'
down_revision: Union[str, Sequence[str], None] = '5c9ca3d9408d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("item_pricelist", "id", new_column_name="pricelist_id", schema="inventory")


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("item_pricelist", "pricelist_id", new_column_name="id", schema="inventory")
