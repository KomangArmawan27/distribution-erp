from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ItemPriceListBase(BaseModel):
    item_id: int
    item_price_ms: Decimal = Field(max_digits=12, decimal_places=2)
    item_price_ws: Decimal = Field(max_digits=12, decimal_places=2)
    item_price_distri: Decimal = Field(max_digits=12, decimal_places=2)


class ItemPriceListCreate(ItemPriceListBase):
    pass


class ItemPriceListUpdate(BaseModel):
    item_id: int | None = None
    item_price_ms: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    item_price_ws: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    item_price_distri: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)


class ItemPriceListRead(ItemPriceListBase):
    model_config = ConfigDict(from_attributes=True)

    pricelist_id: int
    item_no: str | None = None
    item_desc: str | None = None
