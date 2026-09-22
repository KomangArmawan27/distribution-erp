from datetime import date
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PackingListDetailCreate(BaseModel):
    item_id: int
    trans_qty: int = Field(gt=0)


class PackingListDetailUpdate(BaseModel):
    item_id: int | None = None
    trans_qty: int | None = Field(default=None, gt=0)


class PackingListDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trans_id: int
    packing_list_id: int
    trans_idx: int
    item_id: int
    item_no: str | None = None
    item_desc: str | None = None
    trans_qty: int


class PackingListHeaderCreate(BaseModel):
    sales_order_id: int | None = None
    doc_date: date | None = None
    details: list[PackingListDetailCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_items(self):
        if self.details:
            item_ids = [d.item_id for d in self.details]
            if len(item_ids) != len(set(item_ids)):
                raise ValueError("Duplicate item_id found in packing list details. Each item can only appear once per packing list.")
        return self


class PackingListHeaderUpdate(BaseModel):
    sales_order_id: int | None = None
    doc_date: date | None = None
    details: list[PackingListDetailCreate] | None = None

    @model_validator(mode="after")
    def validate_unique_items(self):
        if self.details:
            item_ids = [d.item_id for d in self.details]
            if len(item_ids) != len(set(item_ids)):
                raise ValueError("Duplicate item_id found in packing list details. Each item can only appear once per packing list.")
        return self


class PackingListHeaderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    packing_list_id: int
    packing_list_no: str
    sales_order_id: int | None = None
    sales_order_no: str | None = None
    cust_id: int | None = None
    customer_no: str | None = None
    customer_name: str | None = None
    dropship_id: int | None = None
    dropship_no: str | None = None
    dropship_name: str | None = None
    doctype_id: int
    doc_state: int
    doc_state_display: str | None = None
    doc_date: date
    details: list[PackingListDetailRead] = []
