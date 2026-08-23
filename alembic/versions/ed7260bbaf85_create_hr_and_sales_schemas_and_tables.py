"""create_hr_and_sales_schemas_and_tables

Revision ID: ed7260bbaf85
Revises: 63b865b5ada5
Create Date: 2026-08-23 14:47:53.294194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed7260bbaf85'
down_revision: Union[str, Sequence[str], None] = '63b865b5ada5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS hr")
    op.execute("CREATE SCHEMA IF NOT EXISTS sales")

    op.create_table(
        "employee",
        sa.Column("employee_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("employee_no", sa.String(50), nullable=False),
        sa.Column("employee_name", sa.String(255), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=True),
        sa.Column("department", sa.SmallInteger(), nullable=True),
        sa.Column("join_date", sa.Date(), nullable=True),
        sa.Column("status", sa.SmallInteger(), nullable=True),
        sa.UniqueConstraint("employee_no", name="uq_employee_employee_no"),
        schema="hr",
    )

    op.create_table(
        "sales_person",
        sa.Column("sales_person_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("sales_person_no", sa.String(50), nullable=False),
        sa.Column("sales_area", sa.SmallInteger(), nullable=True),
        sa.Column("sales_level", sa.SmallInteger(), nullable=True),
        sa.Column("status", sa.SmallInteger(), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["hr.employee.employee_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("sales_person_no", name="uq_sales_person_sales_person_no"),
        schema="sales",
    )

    op.create_table(
        "customer",
        sa.Column("customer_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_no", sa.String(50), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("customer_type", sa.SmallInteger(), nullable=True),
        sa.Column("sales_person_id", sa.Integer(), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("city_region", sa.SmallInteger(), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("status", sa.SmallInteger(), nullable=True),
        sa.ForeignKeyConstraint(["sales_person_id"], ["sales.sales_person.sales_person_id"], ondelete="SET NULL"),
        sa.UniqueConstraint("customer_no", name="uq_customer_customer_no"),
        schema="sales",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP SCHEMA IF EXISTS sales CASCADE")
    op.execute("DROP SCHEMA IF EXISTS hr CASCADE")
