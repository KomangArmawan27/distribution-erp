from sqlalchemy import ForeignKey, ForeignKeyConstraint, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DocumentType(Base):
    __tablename__ = "document_type"
    __table_args__ = (
        UniqueConstraint("doctype_code", name="uq_document_type_code"),
        {"schema": "system"},
    )

    doctype_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    doctype_code: Mapped[str] = mapped_column(String(30), nullable=False)
    doctype_name: Mapped[str] = mapped_column(String(100), nullable=False)


class FlowState(Base):
    __tablename__ = "flow_state"
    __table_args__ = (
        UniqueConstraint("doctype_id", "docflow_seq", name="uq_flow_state_doctype_seq"),
        UniqueConstraint("doctype_id", "flow_state", name="uq_flow_state_doctype_label"),
        {"schema": "system"},
    )

    flow_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doctype_id: Mapped[int] = mapped_column(ForeignKey("system.document_type.doctype_id"), nullable=False)
    docflow_seq: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    flow_state: Mapped[str] = mapped_column(String(50), nullable=False)


class FlowTransition(Base):
    __tablename__ = "flow_transition"
    __table_args__ = (
        ForeignKeyConstraint(
            ["doctype_id", "from_seq"], ["system.flow_state.doctype_id", "system.flow_state.docflow_seq"]
        ),
        ForeignKeyConstraint(
            ["doctype_id", "to_seq"], ["system.flow_state.doctype_id", "system.flow_state.docflow_seq"]
        ),
        {"schema": "system"},
    )

    transition_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doctype_id: Mapped[int] = mapped_column(ForeignKey("system.document_type.doctype_id"), nullable=False)
    from_seq: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    to_seq: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    action_label: Mapped[str] = mapped_column(String(50), nullable=False)
    min_role: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
