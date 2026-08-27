"""rename group_value to group_display and add integer group_value

Revision ID: 98a7b6c5d4e3
Revises: 2781c4f12188
Create Date: 2026-08-27 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98a7b6c5d4e3'
down_revision: Union[str, Sequence[str], None] = '2781c4f12188'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('group', 'group_value', new_column_name='group_display', schema='system')
    op.add_column('group', sa.Column('group_value', sa.Integer(), nullable=True), schema='system')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('group', 'group_value', schema='system')
    op.alter_column('group', 'group_display', new_column_name='group_value', schema='system')
