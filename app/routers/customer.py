from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.customer import customer_crud, find_missing_group
from app.crud.sales_person import sales_person_crud
from app.config.database import get_db
from app.utils.pagination import build_links, pagination_dict
from app.utils.response import APIError, success
from app.schemas.envelope import Envelope
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["Customer Master"])


async def _ensure_sales_person_exists(db: AsyncSession, sales_person_id: int | None) -> None:
    if sales_person_id is not None:
        if not await sales_person_crud.get(db, sales_person_id):
            raise APIError(404, "SALES_PERSON_NOT_FOUND", f"Sales person {sales_person_id} not found")


async def _ensure_groups_exist(db: AsyncSession, values: dict) -> None:
    missing = await find_missing_group(db, values)
    if missing:
        group_name, noid = missing
        raise APIError(404, "GROUP_NOT_FOUND", f"Group '{group_name}' noid {noid} not found")


@router.get("/", response_model=Envelope[list[CustomerRead]], response_model_exclude_none=True)
async def list_customers(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    page_result = await customer_crud.page(db, page=page, per_page=per_page)
    data = [CustomerRead.model_validate(obj) for obj in page_result.items]
    return success(
        data,
        "Customers fetched successfully",
        request,
        pagination=pagination_dict(page_result),
        links=build_links(request, page, per_page, page_result),
    )


@router.get("/{customer_id}", response_model=Envelope[CustomerRead], response_model_exclude_none=True)
async def get_customer(customer_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await customer_crud.get(db, customer_id)
    if not obj:
        raise APIError(404, "CUSTOMER_NOT_FOUND", f"Customer {customer_id} not found")
    return success(CustomerRead.model_validate(obj), "Customer fetched successfully", request)


@router.post("/", response_model=Envelope[CustomerRead], response_model_exclude_none=True, status_code=201)
async def create_customer(payload: CustomerCreate, request: Request, db: AsyncSession = Depends(get_db)):
    await _ensure_sales_person_exists(db, payload.sales_person_id)
    await _ensure_groups_exist(db, payload.model_dump())
    obj = await customer_crud.create(db, payload)
    return success(CustomerRead.model_validate(obj), "Customer created successfully", request)


@router.put("/{customer_id}", response_model=Envelope[CustomerRead], response_model_exclude_none=True)
async def update_customer(customer_id: int, payload: CustomerUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await customer_crud.get(db, customer_id)
    if not obj:
        raise APIError(404, "CUSTOMER_NOT_FOUND", f"Customer {customer_id} not found")
    if payload.sales_person_id is not None and payload.sales_person_id != obj.sales_person_id:
        await _ensure_sales_person_exists(db, payload.sales_person_id)
    await _ensure_groups_exist(db, payload.model_dump(exclude_unset=True))
    obj = await customer_crud.update(db, obj, payload)
    return success(CustomerRead.model_validate(obj), "Customer updated successfully", request)


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    ok = await customer_crud.delete(db, customer_id)
    if not ok:
        raise APIError(404, "CUSTOMER_NOT_FOUND", f"Customer {customer_id} not found")
