"""create warehouse schema and packing list tables

Revision ID: 51c8d7e6f4a3
Revises: 40b9c8d7e6f5
Create Date: 2026-09-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51c8d7e6f4a3'
down_revision: Union[str, Sequence[str], None] = '40b9c8d7e6f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create warehouse schema
    op.execute("CREATE SCHEMA IF NOT EXISTS warehouse;")

    # 2. Seed PACKING_LIST document type, flow states, and transitions
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO system.document_type (doctype_id, doctype_code, doctype_name) "
            "VALUES (2, 'PACKING_LIST', 'Packing List') ON CONFLICT (doctype_code) DO NOTHING;"
        )
    )

    states = [
        (2, 1, 'New Entry'),
        (2, 2, 'Documented'),
        (2, 3, 'Approved'),
        (2, 4, 'Rejected'),
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
        (2, 1, 2, 'Submit / Document', 1),
        (2, 2, 3, 'Approve', 1),
        (2, 2, 4, 'Reject', 1),
        (2, 4, 1, 'Reopen / Reset', 1),
    ]
    for dt_id, f_seq, t_seq, label, role in transitions:
        conn.execute(
            sa.text(
                "INSERT INTO system.flow_transition (doctype_id, from_seq, to_seq, action_label, min_role) "
                "VALUES (:dt_id, :f_seq, :t_seq, :label, :role) ON CONFLICT DO NOTHING;"
            ),
            {"dt_id": dt_id, "f_seq": f_seq, "t_seq": t_seq, "label": label, "role": role}
        )

    # 3. Create warehouse.packing_list_header
    op.create_table(
        "packing_list_header",
        sa.Column("packing_list_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("packing_list_no", sa.String(50), nullable=False),
        sa.Column("sales_order_id", sa.Integer(), nullable=True),
        sa.Column("doctype_id", sa.SmallInteger(), nullable=False, server_default="2"),
        sa.Column("doc_state", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("doc_date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["sales_order_id"], ["sales.order_header.doc_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["doctype_id", "doc_state"],
            ["system.flow_state.doctype_id", "system.flow_state.docflow_seq"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("packing_list_no", name="uq_packing_list_header_no"),
        sa.UniqueConstraint("sales_order_id", name="uq_packing_list_header_sales_order"),
        sa.CheckConstraint("doctype_id = 2", name="ck_packing_list_header_doctype"),
        schema="warehouse",
    )

    # 4. Create warehouse.packing_list_detail
    op.create_table(
        "packing_list_detail",
        sa.Column("trans_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("packing_list_id", sa.Integer(), nullable=False),
        sa.Column("trans_idx", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("trans_qty", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["packing_list_id"], ["warehouse.packing_list_header.packing_list_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory.item.item_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("packing_list_id", "item_id", name="uq_packing_list_detail_doc_item"),
        sa.CheckConstraint("trans_qty > 0", name="ck_packing_list_detail_trans_qty_positive"),
        schema="warehouse",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("packing_list_detail", schema="warehouse")
    op.drop_table("packing_list_header", schema="warehouse")
    
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM system.flow_transition WHERE doctype_id = 2;"))
    conn.execute(sa.text("DELETE FROM system.flow_state WHERE doctype_id = 2;"))
    conn.execute(sa.text("DELETE FROM system.document_type WHERE doctype_id = 2;"))
    
    op.execute("DROP SCHEMA IF EXISTS warehouse;")
