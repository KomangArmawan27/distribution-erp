from datetime import date
from decimal import Decimal
from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.customer.models import Customer
from app.modules.sales_person.models import SalesPerson
from app.modules.item.models import Item


class OrderHeader(Base):
    __tablename__ = "order_header"
    __table_args__ = (
        UniqueConstraint("doc_no", name="uq_order_header_doc_no"),
        {"schema": "sales"},
    )

    doc_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_no: Mapped[str] = mapped_column(String(50), nullable=False)
    doc_date: Mapped[date] = mapped_column(Date, nullable=False)
    doc_duedate: Mapped[date] = mapped_column(Date, nullable=False)
    doc_terms: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    cust_id: Mapped[int] = mapped_column(
        ForeignKey("sales.customer.customer_id", ondelete="RESTRICT"), nullable=False
    )
    dropship_id: Mapped[int | None] = mapped_column(
        ForeignKey("sales.customer.customer_id", ondelete="SET NULL"), nullable=True
    )
    sales_id: Mapped[int | None] = mapped_column(
        ForeignKey("sales.sales_person.sales_person_id", ondelete="SET NULL"), nullable=True
    )

    customer: Mapped["Customer"] = relationship("Customer", foreign_keys=[cust_id], lazy="joined")
    dropship_customer: Mapped["Customer | None"] = relationship("Customer", foreign_keys=[dropship_id], lazy="joined")
    sales_person: Mapped["SalesPerson | None"] = relationship("SalesPerson", foreign_keys=[sales_id], lazy="joined")
    details: Mapped[list["OrderDetail"]] = relationship(
        "OrderDetail", back_populates="header", cascade="all, delete-orphan", lazy="selectin"
    )


class OrderDetail(Base):
    __tablename__ = "order_detail"
    __table_args__ = (
        UniqueConstraint("doc_id", "item_id", name="uq_order_detail_doc_item"),
        CheckConstraint("trans_qty > 0", name="ck_order_detail_trans_qty_positive"),
        {"schema": "sales"},
    )

    trans_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = mapped_column(
        ForeignKey("sales.order_header.doc_id", ondelete="CASCADE"), nullable=False
    )
    trans_idx: Mapped[int] = mapped_column(nullable=False)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.item.item_id", ondelete="RESTRICT"), nullable=False
    )
    trans_qty: Mapped[int] = mapped_column(nullable=False)
    trans_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    trans_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    header: Mapped["OrderHeader"] = relationship("OrderHeader", back_populates="details")
    item: Mapped["Item"] = relationship("Item", foreign_keys=[item_id], lazy="joined")
