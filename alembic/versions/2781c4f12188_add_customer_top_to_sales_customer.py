"""add customer_top to sales customer

Revision ID: 2781c4f12188
Revises: ed7260bbaf85
Create Date: 2026-08-27 11:26:23.873072

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2781c4f12188'
down_revision: Union[str, Sequence[str], None] = 'ed7260bbaf85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "customer",
        sa.Column("customer_top", sa.SmallInteger(), nullable=True),
        schema="sales",
    )
    op.add_column(
        "customer",
        sa.Column(
            "customer_top_group_name",
            sa.String(),
            sa.Computed("('CUSTOMER TOP')", persisted=True),
            nullable=True,
        ),
        schema="sales",
    )
    op.create_foreign_key(
        "fk_customer_customer_top_group",
        "customer",
        "group",
        ["customer_top_group_name", "customer_top"],
        ["group_name", "group_noid"],
        source_schema="sales",
        referent_schema="system",
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_customer_customer_top_group", "customer", schema="sales", type_="foreignkey")
    op.drop_column("customer", "customer_top_group_name", schema="sales")
    op.drop_column("customer", "customer_top", schema="sales")
