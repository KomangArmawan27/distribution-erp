"""add customer_type fk to customer

Revision ID: 8c9d0e1f2a3b
Revises: 7a8b9c0d1e2f
Create Date: 2026-09-22 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c9d0e1f2a3b'
down_revision: Union[str, Sequence[str], None] = '7a8b9c0d1e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "customer",
        sa.Column(
            "customer_type_group_name",
            sa.String(),
            sa.Computed("('CUSTOMER TYPE')", persisted=True),
            nullable=True,
        ),
        schema="sales",
    )
    op.create_foreign_key(
        "fk_customer_customer_type_group",
        "customer",
        "group",
        ["customer_type_group_name", "customer_type"],
        ["group_name", "group_noid"],
        source_schema="sales",
        referent_schema="system",
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_customer_customer_type_group", "customer", schema="sales", type_="foreignkey")
    op.drop_column("customer", "customer_type_group_name", schema="sales")
