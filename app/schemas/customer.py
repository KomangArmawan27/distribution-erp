from pydantic import BaseModel, ConfigDict, Field, field_validator


class _UppercaseMixin:
    @field_validator("customer_no")
    @classmethod
    def _to_upper(cls, v):
        if v is None:
            return v
        return str(v).strip().upper()


class CustomerBase(_UppercaseMixin, BaseModel):
    customer_no: str | None = Field(default=None, max_length=50)
    customer_name: str = Field(max_length=255)
    customer_type: int | None = None
    sales_person_id: int | None = None
    address: str | None = Field(default=None, max_length=500)
    city_region: int | None = None
    phone: str | None = Field(default=None, max_length=50)
    status: int | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(_UppercaseMixin, BaseModel):
    customer_no: str | None = Field(default=None, max_length=50)
    customer_name: str | None = Field(default=None, max_length=255)
    customer_type: int | None = None
    sales_person_id: int | None = None
    address: str | None = Field(default=None, max_length=500)
    city_region: int | None = None
    phone: str | None = Field(default=None, max_length=50)
    status: int | None = None


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    customer_type_display: str | None = None
    city_region_display: str | None = None
    status_display: str | None = None
