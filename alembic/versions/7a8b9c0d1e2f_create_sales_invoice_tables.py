"""create sales invoice tables

Revision ID: 7a8b9c0d1e2f
Revises: 51c8d7e6f4a3
Create Date: 2026-09-18 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, Sequence[str], None] = '51c8d7e6f4a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Seed SALES_INVOICE document type, flow states, and transitions
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO system.document_type (doctype_id, doctype_code, doctype_name) "
            "VALUES (3, 'SALES_INVOICE', 'Sales Invoice') ON CONFLICT (doctype_code) DO NOTHING;"
        )
    )

    states = [
        (3, 1, 'New Entry'),
        (3, 2, 'Documented'),
        (3, 3, 'Approved'),
        (3, 4, 'Rejected'),
    ]
    for dt_id, seq, label in states:
        conn.execute(
            sa.text(
                "INSERT INTO system.flow_state (doctype_id, docflow_seq, flow_state) "
                "VALUES (:dt_id, :seq, :label) ON CONFLICT (doctype_id, docflow_seq) DO NOTHING;"
            ),
            {"dt_id": dt_id, "seq": seq, "label": label}
        )

    transitions = [
        (3, 1, 2, 'Submit / Document', 1),
        (3, 2, 3, 'Approve', 1),
        (3, 2, 4, 'Reject', 1),
        (3, 4, 1, 'Reopen / Reset', 1),
    ]
    for dt_id, f_seq, t_seq, label, role in transitions:
        conn.execute(
            sa.text(
                "INSERT INTO system.flow_transition (doctype_id, from_seq, to_seq, action_label, min_role) "
                "VALUES (:dt_id, :f_seq, :t_seq, :label, :role) ON CONFLICT DO NOTHING;"
            ),
            {"dt_id": dt_id, "f_seq": f_seq, "t_seq": t_seq, "label": label, "role": role}
        )

    # 2. Create sales.invoice_header
    op.create_table(
        "invoice_header",
        sa.Column("invoice_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("invoice_no", sa.String(50), nullable=False),
        sa.Column("sales_order_id", sa.Integer(), nullable=True),
        sa.Column("doctype_id", sa.SmallInteger(), nullable=False, server_default="3"),
        sa.Column("doc_state", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("doc_date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["sales_order_id"], ["sales.order_header.doc_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["doctype_id", "doc_state"],
            ["system.flow_state.doctype_id", "system.flow_state.docflow_seq"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("invoice_no", name="uq_invoice_header_no"),
        sa.UniqueConstraint("sales_order_id", name="uq_invoice_header_sales_order"),
        sa.CheckConstraint("doctype_id = 3", name="ck_invoice_header_doctype"),
        schema="sales",
    )

    # 3. Create sales.invoice_detail
    op.create_table(
        "invoice_detail",
        sa.Column("trans_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("trans_idx", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("trans_qty", sa.Integer(), nullable=False),
        sa.Column("item_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("trans_total", sa.Numeric(15, 2), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["sales.invoice_header.invoice_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory.item.item_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("invoice_id", "item_id", name="uq_invoice_detail_doc_item"),
        sa.CheckConstraint("trans_qty > 0", name="ck_invoice_detail_trans_qty_positive"),
        schema="sales",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("invoice_detail", schema="sales")
    op.drop_table("invoice_header", schema="sales")
    
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM system.flow_transition WHERE doctype_id = 3;"))
    conn.execute(sa.text("DELETE FROM system.flow_state WHERE doctype_id = 3;"))
    conn.execute(sa.text("DELETE FROM system.document_type WHERE doctype_id = 3;"))
