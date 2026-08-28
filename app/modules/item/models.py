from sqlalchemy import Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Item(Base):
    __tablename__ = "item"
    __table_args__ = (
        UniqueConstraint("item_no"),
        {"schema": "inventory"},
    )

    item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_no: Mapped[str] = mapped_column(String(50), nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sub_group: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    brand_group: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    series_group: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    flavour_group: Mapped[str] = mapped_column(String(100), nullable=True)
    pack_group: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    ml_group: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    nic_group: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    item_year: Mapped[int] = mapped_column(Integer, nullable=True)
