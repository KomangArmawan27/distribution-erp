"""create sales order tables

Revision ID: 39a8b7c6d5e4
Revises: 98a7b6c5d4e3
Create Date: 2026-08-27 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39a8b7c6d5e4'
down_revision: Union[str, Sequence[str], None] = '98a7b6c5d4e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "order_header",
        sa.Column("doc_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("doc_no", sa.String(50), nullable=False),
        sa.Column("doc_date", sa.Date(), nullable=False),
        sa.Column("doc_duedate", sa.Date(), nullable=False),
        sa.Column("doc_terms", sa.SmallInteger(), nullable=False),
        sa.Column("cust_id", sa.Integer(), nullable=False),
        sa.Column("dropship_id", sa.Integer(), nullable=True),
        sa.Column("sales_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["cust_id"], ["sales.customer.customer_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["dropship_id"], ["sales.customer.customer_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sales_id"], ["sales.sales_person.sales_person_id"], ondelete="SET NULL"),
        sa.UniqueConstraint("doc_no", name="uq_order_header_doc_no"),
        schema="sales",
    )

    op.create_table(
        "order_detail",
        sa.Column("trans_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("doc_id", sa.Integer(), nullable=False),
        sa.Column("trans_idx", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("trans_qty", sa.Integer(), nullable=False),
        sa.Column("trans_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("trans_total", sa.Numeric(15, 2), nullable=False),
        sa.CheckConstraint("trans_qty > 0", name="ck_order_detail_trans_qty_positive"),
        sa.ForeignKeyConstraint(["doc_id"], ["sales.order_header.doc_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory.item.item_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("doc_id", "item_id", name="uq_order_detail_doc_item"),
        schema="sales",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("order_detail", schema="sales")
    op.drop_table("order_header", schema="sales")
