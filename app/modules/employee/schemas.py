from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class EmployeeBase(BaseModel):
    employee_no: str | None = Field(default=None, max_length=50)
    employee_name: str = Field(max_length=255)
    position: int | None = None
    department: int | None = None
    join_date: date | None = None
    status: int | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    employee_no: str | None = Field(default=None, max_length=50)
    employee_name: str | None = Field(default=None, max_length=255)
    position: int | None = None
    department: int | None = None
    join_date: date | None = None
    status: int | None = None


class EmployeeRead(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    position_display: str | None = None
    department_display: str | None = None
    status_display: str | None = None
