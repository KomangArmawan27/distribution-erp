"""create group, item, item_pricelist tables

Revision ID: 5c9ca3d9408d
Revises: 7c67a18f645e
Create Date: 2026-08-11 16:59:14.838858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c9ca3d9408d'
down_revision: Union[str, Sequence[str], None] = '7c67a18f645e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "group",
        sa.Column("group_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("group_noid", sa.SmallInteger(), nullable=False),
        sa.Column("group_name", sa.String(50), nullable=False),
        sa.Column("group_value", sa.String(100), nullable=False),
        sa.UniqueConstraint("group_name", "group_noid", name="uq_group_group_name_noid"),
        schema="system",
    )

    op.create_table(
        "item",
        sa.Column("item_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("item_no", sa.String(50), nullable=False),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column("sub_group", sa.SmallInteger(), nullable=True),
        sa.Column("brand_group", sa.SmallInteger(), nullable=True),
        sa.Column("series_group", sa.SmallInteger(), nullable=True),
        sa.Column("flavour_group", sa.String(100), nullable=True),
        sa.Column("pack_group", sa.SmallInteger(), nullable=True),
        sa.Column("ml_group", sa.SmallInteger(), nullable=True),
        sa.Column("nic_group", sa.SmallInteger(), nullable=True),
        sa.Column("item_year", sa.Integer(), nullable=True),
        sa.UniqueConstraint("item_no", name="uq_item_item_no"),
        schema="inventory",
    )

    op.create_table(
        "item_pricelist",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "item_id",
            sa.Integer(),
            sa.ForeignKey("inventory.item.item_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_price_ms", sa.Numeric(12, 2), nullable=False),
        sa.Column("item_price_ws", sa.Numeric(12, 2), nullable=False),
        sa.Column("item_price_distri", sa.Numeric(12, 2), nullable=False),
        sa.UniqueConstraint("item_id", name="uq_item_pricelist_item_id"),
        schema="inventory",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("item_pricelist", schema="inventory")
    op.drop_table("item", schema="inventory")
    op.drop_table("group", schema="system")
