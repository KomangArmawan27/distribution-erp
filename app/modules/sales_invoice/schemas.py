from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class InvoiceDetailCreate(BaseModel):
    item_id: int
    trans_qty: int = Field(gt=0)


class InvoiceDetailUpdate(BaseModel):
    item_id: int | None = None
    trans_qty: int | None = Field(default=None, gt=0)


class InvoiceDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trans_id: int
    invoice_id: int
    trans_idx: int
    item_id: int
    item_no: str | None = None
    item_desc: str | None = None
    trans_qty: int
    item_price: Decimal
    trans_total: Decimal


class InvoiceHeaderCreate(BaseModel):
    sales_order_id: int | None = None
    customer_id: int | None = None
    doc_date: date | None = None
    details: list[InvoiceDetailCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_items(self):
        if self.details:
            item_ids = [d.item_id for d in self.details]
            if len(item_ids) != len(set(item_ids)):
                raise ValueError("Duplicate item_id found in invoice details. Each item can only appear once per invoice.")
        return self


class InvoiceHeaderUpdate(BaseModel):
    sales_order_id: int | None = None
    customer_id: int | None = None
    doc_date: date | None = None
    details: list[InvoiceDetailCreate] | None = None

    @model_validator(mode="after")
    def validate_unique_items(self):
        if self.details:
            item_ids = [d.item_id for d in self.details]
            if len(item_ids) != len(set(item_ids)):
                raise ValueError("Duplicate item_id found in invoice details. Each item can only appear once per invoice.")
        return self


class InvoiceHeaderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invoice_id: int
    invoice_no: str
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
    invoice_total: Decimal
    details: list[InvoiceDetailRead] = []
