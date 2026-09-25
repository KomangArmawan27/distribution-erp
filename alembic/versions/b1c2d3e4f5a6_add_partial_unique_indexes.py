"""add_partial_unique_indexes

Revision ID: b1c2d3e4f5a6
Revises: 9a1b2c3d4e5f
Create Date: 2026-09-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = '9a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Drop old unique constraints
    op.drop_constraint('uq_invoice_header_sales_order', 'invoice_header', schema='sales', type_='unique')
    op.drop_constraint('uq_packing_list_header_sales_order', 'packing_list_header', schema='warehouse', type_='unique')

    # 2. Create partial unique indexes where doc_state != 5
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_invoice_header_sales_order "
            "ON sales.invoice_header (sales_order_id) "
            "WHERE doc_state != 5;"
        )
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_packing_list_header_sales_order "
            "ON warehouse.packing_list_header (sales_order_id) "
            "WHERE doc_state != 5;"
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("DROP INDEX IF EXISTS sales.uq_invoice_header_sales_order;"))
    op.execute(sa.text("DROP INDEX IF EXISTS warehouse.uq_packing_list_header_sales_order;"))
    
    op.create_unique_constraint('uq_invoice_header_sales_order', 'invoice_header', ['sales_order_id'], schema='sales')
    op.create_unique_constraint('uq_packing_list_header_sales_order', 'packing_list_header', ['sales_order_id'], schema='warehouse')
