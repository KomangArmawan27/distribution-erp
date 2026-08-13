from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class ItemPriceList(Base):
    __tablename__ = "item_pricelist"
    __table_args__ = (
        UniqueConstraint("item_id"),
        {"schema": "inventory"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.item.item_id", ondelete="CASCADE"), nullable=False
    )
    item_price_ms: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    item_price_ws: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    item_price_distri: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)