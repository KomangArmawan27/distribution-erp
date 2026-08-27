from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.sales_order import sales_order_crud
from app.crud.customer import customer_crud
from app.crud.sales_person import sales_person_crud
from app.crud.item import item_crud
from app.config.database import get_db
from app.models import Group
from app.utils.pagination import build_links, pagination_dict
from app.utils.response import APIError, success
from app.schemas.envelope import Envelope
from app.schemas.sales_order import OrderHeaderCreate, OrderHeaderRead, OrderHeaderUpdate

router = APIRouter(prefix="/sales-orders", tags=["Sales Orders"])


async def _ensure_relations_exist(db: AsyncSession, cust_id: int, doc_terms: int, dropship_id: int | None, sales_id: int | None, details: list) -> None:
    if not await customer_crud.get(db, cust_id):
        raise APIError(404, "CUSTOMER_NOT_FOUND", f"Customer {cust_id} not found")
    if dropship_id is not None:
        if not await customer_crud.get(db, dropship_id):
            raise APIError(404, "CUSTOMER_NOT_FOUND", f"Dropship customer {dropship_id} not found")
    if sales_id is not None:
        if not await sales_person_crud.get(db, sales_id):
            raise APIError(404, "SALES_PERSON_NOT_FOUND", f"Sales person {sales_id} not found")
    
    res = await db.execute(
        select(Group.group_id).where(Group.group_name == "CUSTOMER TOP", Group.group_noid == doc_terms)
    )
    if res.scalar_one_or_none() is None:
        raise APIError(404, "GROUP_NOT_FOUND", f"Group 'CUSTOMER TOP' noid {doc_terms} not found")

    for det in details:
        if not await item_crud.get(db, det.item_id):
            raise APIError(404, "ITEM_NOT_FOUND", f"Item {det.item_id} not found")


@router.get("/", response_model=Envelope[list[OrderHeaderRead]], response_model_exclude_none=True)
async def list_sales_orders(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    page_result = await sales_order_crud.page(db, page=page, per_page=per_page)
    data = [OrderHeaderRead.model_validate(obj) for obj in page_result.items]
    return success(
        data,
        "Sales orders fetched successfully",
        request,
        pagination=pagination_dict(page_result),
        links=build_links(request, page, per_page, page_result),
    )


@router.get("/{doc_id}", response_model=Envelope[OrderHeaderRead], response_model_exclude_none=True)
async def get_sales_order(doc_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await sales_order_crud.get(db, doc_id)
    if not obj:
        raise APIError(404, "SALES_ORDER_NOT_FOUND", f"Sales order {doc_id} not found")
    return success(OrderHeaderRead.model_validate(obj), "Sales order fetched successfully", request)


@router.post("/", response_model=Envelope[OrderHeaderRead], response_model_exclude_none=True, status_code=201)
async def create_sales_order(payload: OrderHeaderCreate, request: Request, db: AsyncSession = Depends(get_db)):
    await _ensure_relations_exist(
        db, payload.cust_id, payload.doc_terms, payload.dropship_id, payload.sales_id, payload.details
    )
    try:
        obj = await sales_order_crud.create(db, payload)
    except ValueError as e:
        raise APIError(422, "VALIDATION_ERROR", "Validation failed", [{"field": "sales_order", "message": str(e)}])
    return success(OrderHeaderRead.model_validate(obj), "Sales order created successfully", request)


@router.put("/{doc_id}", response_model=Envelope[OrderHeaderRead], response_model_exclude_none=True)
async def update_sales_order(doc_id: int, payload: OrderHeaderUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await sales_order_crud.get(db, doc_id)
    if not obj:
        raise APIError(404, "SALES_ORDER_NOT_FOUND", f"Sales order {doc_id} not found")

    cust_id = payload.cust_id if payload.cust_id is not None else obj.cust_id
    doc_terms = payload.doc_terms if payload.doc_terms is not None else obj.doc_terms
    dropship_id = payload.dropship_id if payload.dropship_id is not None else obj.dropship_id
    sales_id = payload.sales_id if payload.sales_id is not None else obj.sales_id
    details = payload.details if payload.details is not None else obj.details

    await _ensure_relations_exist(db, cust_id, doc_terms, dropship_id, sales_id, details)
    
    try:
        obj = await sales_order_crud.update(db, obj, payload)
    except ValueError as e:
        raise APIError(422, "VALIDATION_ERROR", "Validation failed", [{"field": "sales_order", "message": str(e)}])
    return success(OrderHeaderRead.model_validate(obj), "Sales order updated successfully", request)


@router.delete("/{doc_id}", status_code=204)
async def delete_sales_order(doc_id: int, db: AsyncSession = Depends(get_db)):
    ok = await sales_order_crud.delete(db, doc_id)
    if not ok:
        raise APIError(404, "SALES_ORDER_NOT_FOUND", f"Sales order {doc_id} not found")
