from datetime import date
from sqlalchemy import Date, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Employee(Base):
    __tablename__ = "employee"
    __table_args__ = (
        UniqueConstraint("employee_no"),
        {"schema": "hr"},
    )

    employee_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_no: Mapped[str] = mapped_column(String(50), nullable=False)
    employee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    department: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    join_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
