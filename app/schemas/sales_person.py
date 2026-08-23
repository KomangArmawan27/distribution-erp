from pydantic import BaseModel, ConfigDict, Field


class SalesPersonBase(BaseModel):
    employee_id: int
    sales_person_no: str | None = Field(default=None, max_length=50)
    sales_area: int | None = None
    sales_level: int | None = None
    status: int | None = None


class SalesPersonCreate(SalesPersonBase):
    pass


class SalesPersonUpdate(BaseModel):
    employee_id: int | None = None
    sales_person_no: str | None = Field(default=None, max_length=50)
    sales_area: int | None = None
    sales_level: int | None = None
    status: int | None = None


class SalesPersonRead(SalesPersonBase):
    model_config = ConfigDict(from_attributes=True)

    sales_person_id: int
    sales_area_display: str | None = None
    sales_level_display: str | None = None
    status_display: str | None = None
