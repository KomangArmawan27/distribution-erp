from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.employee import employee_crud
from app.crud.sales_person import sales_person_crud
from app.config.database import get_db
from app.utils.pagination import build_links, pagination_dict
from app.utils.response import APIError, success
from app.schemas.envelope import Envelope
from app.schemas.sales_person import SalesPersonCreate, SalesPersonRead, SalesPersonUpdate

router = APIRouter(prefix="/sales-persons", tags=["Sales Person Master"])


async def _ensure_employee_exists(db: AsyncSession, employee_id: int) -> None:
    if not await employee_crud.get(db, employee_id):
        raise APIError(404, "EMPLOYEE_NOT_FOUND", f"Employee {employee_id} not found")


@router.get("/", response_model=Envelope[list[SalesPersonRead]], response_model_exclude_none=True)
async def list_sales_persons(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    page_result = await sales_person_crud.page(db, page=page, per_page=per_page)
    data = [SalesPersonRead.model_validate(obj) for obj in page_result.items]
    return success(
        data,
        "Sales persons fetched successfully",
        request,
        pagination=pagination_dict(page_result),
        links=build_links(request, page, per_page, page_result),
    )


@router.get("/{sales_person_id}", response_model=Envelope[SalesPersonRead], response_model_exclude_none=True)
async def get_sales_person(sales_person_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await sales_person_crud.get(db, sales_person_id)
    if not obj:
        raise APIError(404, "SALES_PERSON_NOT_FOUND", f"Sales person {sales_person_id} not found")
    return success(SalesPersonRead.model_validate(obj), "Sales person fetched successfully", request)


@router.post("/", response_model=Envelope[SalesPersonRead], response_model_exclude_none=True, status_code=201)
async def create_sales_person(payload: SalesPersonCreate, request: Request, db: AsyncSession = Depends(get_db)):
    await _ensure_employee_exists(db, payload.employee_id)
    obj = await sales_person_crud.create(db, payload)
    return success(SalesPersonRead.model_validate(obj), "Sales person created successfully", request)


@router.put("/{sales_person_id}", response_model=Envelope[SalesPersonRead], response_model_exclude_none=True)
async def update_sales_person(sales_person_id: int, payload: SalesPersonUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await sales_person_crud.get(db, sales_person_id)
    if not obj:
        raise APIError(404, "SALES_PERSON_NOT_FOUND", f"Sales person {sales_person_id} not found")
    if payload.employee_id is not None and payload.employee_id != obj.employee_id:
        await _ensure_employee_exists(db, payload.employee_id)
    obj = await sales_person_crud.update(db, obj, payload)
    return success(SalesPersonRead.model_validate(obj), "Sales person updated successfully", request)


@router.delete("/{sales_person_id}", status_code=204)
async def delete_sales_person(sales_person_id: int, db: AsyncSession = Depends(get_db)):
    ok = await sales_person_crud.delete(db, sales_person_id)
    if not ok:
        raise APIError(404, "SALES_PERSON_NOT_FOUND", f"Sales person {sales_person_id} not found")
