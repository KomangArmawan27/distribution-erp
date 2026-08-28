from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employee.crud import employee_crud, find_missing_group
from app.core.database import get_db
from app.core.pagination import build_links, pagination_dict
from app.core.response import APIError, success
from app.core.envelope import Envelope
from app.modules.employee.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate

router = APIRouter(prefix="/employees", tags=["Employee Master"])


async def _ensure_groups_exist(db: AsyncSession, values: dict) -> None:
    missing = await find_missing_group(db, values)
    if missing:
        group_name, noid = missing
        raise APIError(404, "GROUP_NOT_FOUND", f"Group '{group_name}' noid {noid} not found")


@router.get("/", response_model=Envelope[list[EmployeeRead]], response_model_exclude_none=True)
async def list_employees(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    page_result = await employee_crud.page(db, page=page, per_page=per_page)
    data = [EmployeeRead.model_validate(obj) for obj in page_result.items]
    return success(
        data,
        "Employees fetched successfully",
        request,
        pagination=pagination_dict(page_result),
        links=build_links(request, page, per_page, page_result),
    )


@router.get("/{employee_id}", response_model=Envelope[EmployeeRead], response_model_exclude_none=True)
async def get_employee(employee_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await employee_crud.get(db, employee_id)
    if not obj:
        raise APIError(404, "EMPLOYEE_NOT_FOUND", f"Employee {employee_id} not found")
    return success(EmployeeRead.model_validate(obj), "Employee fetched successfully", request)


@router.post("/", response_model=Envelope[EmployeeRead], response_model_exclude_none=True, status_code=201)
async def create_employee(payload: EmployeeCreate, request: Request, db: AsyncSession = Depends(get_db)):
    await _ensure_groups_exist(db, payload.model_dump())
    obj = await employee_crud.create(db, payload)
    return success(EmployeeRead.model_validate(obj), "Employee created successfully", request)


@router.put("/{employee_id}", response_model=Envelope[EmployeeRead], response_model_exclude_none=True)
async def update_employee(employee_id: int, payload: EmployeeUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await employee_crud.get(db, employee_id)
    if not obj:
        raise APIError(404, "EMPLOYEE_NOT_FOUND", f"Employee {employee_id} not found")
    await _ensure_groups_exist(db, payload.model_dump(exclude_unset=True))
    obj = await employee_crud.update(db, obj, payload)
    return success(EmployeeRead.model_validate(obj), "Employee updated successfully", request)


@router.delete("/{employee_id}", status_code=204)
async def delete_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    ok = await employee_crud.delete(db, employee_id)
    if not ok:
        raise APIError(404, "EMPLOYEE_NOT_FOUND", f"Employee {employee_id} not found")
