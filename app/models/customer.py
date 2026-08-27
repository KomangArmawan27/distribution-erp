from sqlalchemy import ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.sales_person import SalesPerson


class Customer(Base):
    __tablename__ = "customer"
    __table_args__ = (
        UniqueConstraint("customer_no"),
        {"schema": "sales"},
    )

    customer_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_no: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_type: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    customer_top: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    sales_person_id: Mapped[int | None] = mapped_column(
        ForeignKey("sales.sales_person.sales_person_id", ondelete="SET NULL"), nullable=True
    )
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city_region: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    sales_person: Mapped["SalesPerson | None"] = relationship("SalesPerson", foreign_keys=[sales_person_id], lazy="joined")
