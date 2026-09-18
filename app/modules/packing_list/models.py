from datetime import date
from sqlalchemy import CheckConstraint, Date, ForeignKey, ForeignKeyConstraint, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.sales_order.models import OrderHeader
from app.modules.item.models import Item


class PackingListHeader(Base):
    __tablename__ = "packing_list_header"
    __table_args__ = (
        UniqueConstraint("packing_list_no", name="uq_packing_list_header_no"),
        UniqueConstraint("sales_order_id", name="uq_packing_list_header_sales_order"),
        CheckConstraint("doctype_id = 2", name="ck_packing_list_header_doctype"),
        ForeignKeyConstraint(
            ["doctype_id", "doc_state"],
            ["system.flow_state.doctype_id", "system.flow_state.docflow_seq"],
            ondelete="RESTRICT",
        ),
        {"schema": "warehouse"},
    )

    packing_list_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    packing_list_no: Mapped[str] = mapped_column(String(50), nullable=False)
    sales_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("sales.order_header.doc_id", ondelete="SET NULL"), nullable=True
    )
    doctype_id: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=2)
    doc_state: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    doc_date: Mapped[date] = mapped_column(Date, nullable=False)

    sales_order: Mapped["OrderHeader | None"] = relationship("OrderHeader", foreign_keys=[sales_order_id], uselist=False, lazy="joined")
    details: Mapped[list["PackingListDetail"]] = relationship(
        "PackingListDetail", back_populates="header", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def sales_order_no(self) -> str | None:
        return self.sales_order.doc_no if self.sales_order else None

    @property
    def cust_id(self) -> int | None:
        return self.sales_order.cust_id if self.sales_order else None

    @property
    def customer_no(self) -> str | None:
        return self.sales_order.customer_no if self.sales_order else None

    @property
    def customer_name(self) -> str | None:
        return self.sales_order.customer_name if self.sales_order else None

    @property
    def dropship_id(self) -> int | None:
        return self.sales_order.dropship_id if self.sales_order else None

    @property
    def dropship_no(self) -> str | None:
        return self.sales_order.dropship_no if self.sales_order else None

    @property
    def dropship_name(self) -> str | None:
        return self.sales_order.dropship_name if self.sales_order else None


class PackingListDetail(Base):
    __tablename__ = "packing_list_detail"
    __table_args__ = (
        UniqueConstraint("packing_list_id", "item_id", name="uq_packing_list_detail_doc_item"),
        CheckConstraint("trans_qty > 0", name="ck_packing_list_detail_trans_qty_positive"),
        {"schema": "warehouse"},
    )

    trans_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    packing_list_id: Mapped[int] = mapped_column(
        ForeignKey("warehouse.packing_list_header.packing_list_id", ondelete="CASCADE"), nullable=False
    )
    trans_idx: Mapped[int] = mapped_column(nullable=False)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.item.item_id", ondelete="RESTRICT"), nullable=False
    )
    trans_qty: Mapped[int] = mapped_column(nullable=False)

    header: Mapped["PackingListHeader"] = relationship("PackingListHeader", back_populates="details")
    item: Mapped["Item"] = relationship("Item", foreign_keys=[item_id], lazy="joined")

    @property
    def item_no(self) -> str | None:
        return self.item.item_no if self.item else None

    @property
    def item_desc(self) -> str | None:
        return self.item.item_name if self.item else None
