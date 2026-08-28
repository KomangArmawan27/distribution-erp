from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.item.models import Item


class ItemPriceList(Base):
    __tablename__ = "item_pricelist"
    __table_args__ = (
        UniqueConstraint("item_id"),
        {"schema": "inventory"},
    )

    pricelist_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.item.item_id", ondelete="CASCADE"), nullable=False
    )
    item_price_ms: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    item_price_ws: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    item_price_distri: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    item: Mapped["Item"] = relationship("Item", foreign_keys=[item_id])

    @property
    def item_no(self) -> str | None:
        return self.item.item_no if self.item else None

    @property
    def item_desc(self) -> str | None:
        return self.item.item_name if self.item else None
