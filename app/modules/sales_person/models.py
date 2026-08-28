from sqlalchemy import ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.employee.models import Employee


class SalesPerson(Base):
    __tablename__ = "sales_person"
    __table_args__ = (
        UniqueConstraint("sales_person_no"),
        {"schema": "sales"},
    )

    sales_person_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("hr.employee.employee_id", ondelete="CASCADE"), nullable=False
    )
    sales_person_no: Mapped[str] = mapped_column(String(50), nullable=False)
    sales_area: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    sales_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    status: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    employee: Mapped["Employee"] = relationship("Employee", foreign_keys=[employee_id], lazy="joined")
