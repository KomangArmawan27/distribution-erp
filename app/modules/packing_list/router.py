from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.envelope import Envelope
from app.core.pagination import build_links, pagination_dict
from app.core.response import APIError, success
from app.modules.packing_list.crud import packing_list_crud, advance_packing_list_state
from app.modules.packing_list.models import PackingListHeader
from app.modules.packing_list.schemas import (
    PackingListHeaderCreate,
    PackingListHeaderRead,
    PackingListHeaderUpdate,
)
from app.modules.sales_order.crud import sales_order_crud
from app.modules.system.schemas import StateUpdateIn

router = APIRouter(prefix="/packing-lists", tags=["Packing Lists"])


@router.get("/", response_model=Envelope[list[PackingListHeaderRead]], response_model_exclude_none=True)
async def list_packing_lists(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    page_result = await packing_list_crud.page(db, page=page, per_page=per_page)
    data = [PackingListHeaderRead.model_validate(obj) for obj in page_result.items]
    return success(
        data,
        "Packing lists fetched successfully",
        request,
        pagination=pagination_dict(page_result),
        links=build_links(request, page, per_page, page_result),
    )


@router.get("/{packing_list_id}", response_model=Envelope[PackingListHeaderRead], response_model_exclude_none=True)
async def get_packing_list(packing_list_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await packing_list_crud.get(db, packing_list_id)
    if not obj:
        raise APIError(404, "PACKING_LIST_NOT_FOUND", f"Packing list {packing_list_id} not found")
    return success(PackingListHeaderRead.model_validate(obj), "Packing list fetched successfully", request)


@router.post("/", response_model=Envelope[PackingListHeaderRead], response_model_exclude_none=True, status_code=201)
async def create_packing_list(payload: PackingListHeaderCreate, request: Request, db: AsyncSession = Depends(get_db)):
    if payload.sales_order_id is not None:
        so = await sales_order_crud.get(db, payload.sales_order_id)
        if not so:
            raise APIError(404, "SALES_ORDER_NOT_FOUND", f"Sales order {payload.sales_order_id} not found")
        existing_pl = (await db.execute(
            select(PackingListHeader).where(PackingListHeader.sales_order_id == payload.sales_order_id)
        )).scalar_one_or_none()
        if existing_pl:
            raise APIError(
                409,
                "SALES_ORDER_ALREADY_PACKED",
                f"Sales order {payload.sales_order_id} already has an associated packing list ({existing_pl.packing_list_no})",
            )
    try:
        obj = await packing_list_crud.create(db, payload)
    except IntegrityError:
        await db.rollback()
        raise APIError(
            409,
            "SALES_ORDER_ALREADY_PACKED",
            f"Sales order {payload.sales_order_id} already has an associated packing list",
        )
    except ValueError as e:
        raise APIError(422, "VALIDATION_ERROR", "Validation failed", [{"field": "packing_list", "message": str(e)}])
    return success(PackingListHeaderRead.model_validate(obj), "Packing list created successfully", request)


@router.put("/{packing_list_id}", response_model=Envelope[PackingListHeaderRead], response_model_exclude_none=True)
async def update_packing_list(
    packing_list_id: int,
    payload: PackingListHeaderUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    obj = await packing_list_crud.get(db, packing_list_id)
    if not obj:
        raise APIError(404, "PACKING_LIST_NOT_FOUND", f"Packing list {packing_list_id} not found")

    if obj.doc_state > 1:
        raise APIError(
            409,
            "DOCUMENT_STATE_LOCKED",
            "Cannot update packing list after it has progressed past 'New Entry'.",
        )

    if payload.sales_order_id is not None:
        so = await sales_order_crud.get(db, payload.sales_order_id)
        if not so:
            raise APIError(404, "SALES_ORDER_NOT_FOUND", f"Sales order {payload.sales_order_id} not found")
        if payload.sales_order_id != obj.sales_order_id:
            existing_pl = (await db.execute(
                select(PackingListHeader).where(PackingListHeader.sales_order_id == payload.sales_order_id)
            )).scalar_one_or_none()
            if existing_pl:
                raise APIError(
                    409,
                    "SALES_ORDER_ALREADY_PACKED",
                    f"Sales order {payload.sales_order_id} already has an associated packing list ({existing_pl.packing_list_no})",
                )

    try:
        obj = await packing_list_crud.update(db, obj, payload)
    except IntegrityError:
        await db.rollback()
        raise APIError(
            409,
            "SALES_ORDER_ALREADY_PACKED",
            f"Sales order {payload.sales_order_id} already has an associated packing list",
        )
    except ValueError as e:
        raise APIError(422, "VALIDATION_ERROR", "Validation failed", [{"field": "packing_list", "message": str(e)}])
    return success(PackingListHeaderRead.model_validate(obj), "Packing list updated successfully", request)


@router.patch("/{packing_list_id}/state", response_model=Envelope[PackingListHeaderRead], response_model_exclude_none=True)
async def update_packing_list_state(
    packing_list_id: int,
    body: StateUpdateIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    obj = await advance_packing_list_state(db, packing_list_id, body.to_seq)
    return success(PackingListHeaderRead.model_validate(obj), "Packing list state updated successfully", request)


@router.delete("/{packing_list_id}", status_code=204)
async def delete_packing_list(packing_list_id: int, db: AsyncSession = Depends(get_db)):
    obj = await packing_list_crud.get(db, packing_list_id)
    if not obj:
        raise APIError(404, "PACKING_LIST_NOT_FOUND", f"Packing list {packing_list_id} not found")

    if obj.doc_state > 1:
        raise APIError(
            409,
            "DOCUMENT_STATE_LOCKED",
            "Cannot delete packing list in state other than 'New Entry'.",
        )

    ok = await packing_list_crud.delete(db, packing_list_id)
    if not ok:
        raise APIError(404, "PACKING_LIST_NOT_FOUND", f"Packing list {packing_list_id} not found")
