from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    item_no: str | None = Field(default=None, max_length=50)
    sub_group: int | None = None
    brand_group: int | None = None
    series_group: int | None = None
    flavour_group: str | None = Field(default=None, max_length=100)
    pack_group: int | None = None
    ml_group: int | None = None
    nic_group: int | None = None
    item_year: int | None = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    item_no: str | None = Field(default=None, max_length=50)
    sub_group: int | None = None
    brand_group: int | None = None
    series_group: int | None = None
    flavour_group: str | None = Field(default=None, max_length=100)
    pack_group: int | None = Field(default=None, max_length=50)
    ml_group: int | None = None
    nic_group: int | None = None
    item_year: int | None = None


class ItemRead(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    item_name: str
    item_no: str