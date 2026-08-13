from sqlalchemy import SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class Group(Base):
    __tablename__ = "group"
    __table_args__ = (UniqueConstraint("group_name", "group_noid"), {"schema": "system"})

    group_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_noid: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    group_name: Mapped[str] = mapped_column(String(50), nullable=False)
    group_value: Mapped[str] = mapped_column(String(100), nullable=False)