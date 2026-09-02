"""add document flow state system

Revision ID: 40b9c8d7e6f5
Revises: 39a8b7c6d5e4
Create Date: 2026-09-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40b9c8d7e6f5'
down_revision: Union[str, Sequence[str], None] = '39a8b7c6d5e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create system.document_type
    op.create_table(
        "document_type",
        sa.Column("doctype_id", sa.SmallInteger(), primary_key=True, autoincrement=True),
        sa.Column("doctype_code", sa.String(30), nullable=False),
        sa.Column("doctype_name", sa.String(100), nullable=False),
        sa.UniqueConstraint("doctype_code", name="uq_document_type_code"),
        schema="system",
    )

    # 2. Create system.flow_state
    op.create_table(
        "flow_state",
        sa.Column("flow_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("doctype_id", sa.SmallInteger(), nullable=False),
        sa.Column("docflow_seq", sa.SmallInteger(), nullable=False),
        sa.Column("flow_state", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["doctype_id"], ["system.document_type.doctype_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("doctype_id", "docflow_seq", name="uq_flow_state_doctype_seq"),
        sa.UniqueConstraint("doctype_id", "flow_state", name="uq_flow_state_doctype_label"),
        schema="system",
    )

    # 3. Create system.flow_transition
    op.create_table(
        "flow_transition",
        sa.Column("transition_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("doctype_id", sa.SmallInteger(), nullable=False),
        sa.Column("from_seq", sa.SmallInteger(), nullable=False),
        sa.Column("to_seq", sa.SmallInteger(), nullable=False),
        sa.Column("action_label", sa.String(50), nullable=False),
        sa.Column("min_role", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["doctype_id"], ["system.document_type.doctype_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["doctype_id", "from_seq"],
            ["system.flow_state.doctype_id", "system.flow_state.docflow_seq"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["doctype_id", "to_seq"],
            ["system.flow_state.doctype_id", "system.flow_state.docflow_seq"],
            ondelete="RESTRICT",
        ),
        schema="system",
    )

    # 4. Seed initial data BEFORE adding foreign keys referencing these tables
    conn = op.get_bind()
    
    # Seed document_type
    conn.execute(
        sa.text(
            "INSERT INTO system.document_type (doctype_id, doctype_code, doctype_name) "
            "VALUES (1, 'SALES_ORDER', 'Sales Order') ON CONFLICT (doctype_code) DO NOTHING;"
        )
    )

    # Seed flow_state for SALES_ORDER (doctype_id = 1)
    states = [
        (1, 1, 'New Entry'),
        (1, 2, 'Documented'),
        (1, 3, 'Approved'),
        (1, 4, 'Rejected'),
    ]
    for dt_id, seq, label in states:
        conn.execute(
            sa.text(
                "INSERT INTO system.flow_state (doctype_id, docflow_seq, flow_state) "
                "VALUES (:dt_id, :seq, :label) ON CONFLICT (doctype_id, docflow_seq) DO NOTHING;"
            ),
            {"dt_id": dt_id, "seq": seq, "label": label}
        )

    # Seed flow_transition for SALES_ORDER (doctype_id = 1)
    transitions = [
        (1, 1, 2, 'Submit / Document', 1),
        (1, 2, 3, 'Approve', 1),
        (1, 2, 4, 'Reject', 1),
        (1, 4, 1, 'Reopen / Reset', 1),
    ]
    for dt_id, f_seq, t_seq, label, role in transitions:
        conn.execute(
            sa.text(
                "INSERT INTO system.flow_transition (doctype_id, from_seq, to_seq, action_label, min_role) "
                "VALUES (:dt_id, :f_seq, :t_seq, :label, :role) ON CONFLICT DO NOTHING;"
            ),
            {"dt_id": dt_id, "f_seq": f_seq, "t_seq": t_seq, "label": label, "role": role}
        )

    # 5. Alter sales.order_header to add doctype_id and doc_state
    op.add_column(
        "order_header",
        sa.Column("doctype_id", sa.SmallInteger(), nullable=False, server_default="1"),
        schema="sales",
    )
    op.add_column(
        "order_header",
        sa.Column("doc_state", sa.SmallInteger(), nullable=False, server_default="1"),
        schema="sales",
    )
    op.create_check_constraint(
        "ck_order_header_doctype",
        "order_header",
        "doctype_id = 1",
        schema="sales",
    )
    op.create_foreign_key(
        "fk_order_header_flow_state",
        "order_header",
        "flow_state",
        ["doctype_id", "doc_state"],
        ["doctype_id", "docflow_seq"],
        source_schema="sales",
        referent_schema="system",
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_order_header_flow_state", "order_header", type_="foreignkey", schema="sales")
    op.drop_constraint("ck_order_header_doctype", "order_header", type_="check", schema="sales")
    op.drop_column("order_header", "doc_state", schema="sales")
    op.drop_column("order_header", "doctype_id", schema="sales")
    
    op.drop_table("flow_transition", schema="system")
    op.drop_table("flow_state", schema="system")
    op.drop_table("document_type", schema="system")
