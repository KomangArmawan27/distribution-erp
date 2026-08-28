from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrderDetailCreate(BaseModel):
    item_id: int
    trans_qty: int = Field(gt=0)
    trans_price: Decimal = Field(max_digits=15, decimal_places=2)


class OrderDetailUpdate(BaseModel):
    item_id: int | None = None
    trans_qty: int | None = Field(default=None, gt=0)
    trans_price: Decimal | None = Field(default=None, max_digits=15, decimal_places=2)


class OrderDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trans_id: int
    doc_id: int
    trans_idx: int
    item_id: int
    item_no: str | None = None
    item_desc: str | None = None
    trans_qty: int
    trans_price: Decimal
    trans_total: Decimal


class OrderHeaderCreate(BaseModel):
    cust_id: int
    doc_terms: int
    dropship_id: int | None = None
    sales_id: int | None = None
    doc_date: date | None = None
    details: list[OrderDetailCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_items(self):
        if self.details:
            item_ids = [d.item_id for d in self.details]
            if len(item_ids) != len(set(item_ids)):
                raise ValueError("Duplicate item_id found in order details. Each item can only appear once per order.")
        return self


class OrderHeaderUpdate(BaseModel):
    cust_id: int | None = None
    doc_terms: int | None = None
    dropship_id: int | None = None
    sales_id: int | None = None
    doc_date: date | None = None
    details: list[OrderDetailCreate] | None = None

    @model_validator(mode="after")
    def validate_unique_items(self):
        if self.details:
            item_ids = [d.item_id for d in self.details]
            if len(item_ids) != len(set(item_ids)):
                raise ValueError("Duplicate item_id found in order details. Each item can only appear once per order.")
        return self


class OrderHeaderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doc_id: int
    doc_no: str
    doc_date: date
    doc_duedate: date
    doc_terms: int
    doc_terms_display: str | None = None
    cust_id: int
    dropship_id: int | None = None
    sales_id: int | None = None
    details: list[OrderDetailRead] = []
