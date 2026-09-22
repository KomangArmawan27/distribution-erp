"""add_is_final_to_flow_state

Revision ID: 9a1b2c3d4e5f
Revises: 8c9d0e1f2a3b
Create Date: 2026-09-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '8c9d0e1f2a3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add is_final column to system.flow_state
    op.add_column(
        "flow_state",
        sa.Column("is_final", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="system",
    )

    # 2. Mark docflow_seq = 3 as final for all document types (Sales Order, Packing List, Sales Invoice)
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE system.flow_state SET is_final = TRUE WHERE docflow_seq = 3;")
    )

    # 3. Insert backward transition: Documented (2) -> New Entry (1) ('Revise') for all document types
    for dt_id in [1, 2, 3]:
        conn.execute(
            sa.text(
                "INSERT INTO system.flow_transition (doctype_id, from_seq, to_seq, action_label, min_role) "
                "VALUES (:dt_id, 2, 1, 'Revise', 1) ON CONFLICT DO NOTHING;"
            ),
            {"dt_id": dt_id}
        )


def downgrade() -> None:
    """Downgrade schema."""
    for dt_id in [1, 2, 3]:
        conn = op.get_bind()
        conn.execute(
            sa.text("DELETE FROM system.flow_transition WHERE doctype_id = :dt_id AND from_seq = 2 AND to_seq = 1;"),
            {"dt_id": dt_id}
        )
    op.drop_column("flow_state", "is_final", schema="system")
