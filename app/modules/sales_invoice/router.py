from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.envelope import Envelope
from app.core.pagination import build_links, pagination_dict
from app.core.response import APIError, success
from app.modules.sales_invoice.crud import sales_invoice_crud, advance_invoice_state
from app.modules.sales_invoice.models import InvoiceHeader
from app.modules.sales_invoice.schemas import (
    InvoiceHeaderCreate,
    InvoiceHeaderRead,
    InvoiceHeaderUpdate,
)
from app.modules.sales_order.crud import sales_order_crud
from app.modules.packing_list.models import PackingListHeader
from app.modules.system.schemas import StateUpdateIn

router = APIRouter(prefix="/sales-invoices", tags=["Sales Invoices"])


@router.get("/", response_model=Envelope[list[InvoiceHeaderRead]], response_model_exclude_none=True)
async def list_sales_invoices(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    page_result = await sales_invoice_crud.page(db, page=page, per_page=per_page)
    data = [InvoiceHeaderRead.model_validate(obj) for obj in page_result.items]
    return success(
        data,
        "Sales invoices fetched successfully",
        request,
        pagination=pagination_dict(page_result),
        links=build_links(request, page, per_page, page_result),
    )


@router.get("/{invoice_id}", response_model=Envelope[InvoiceHeaderRead], response_model_exclude_none=True)
async def get_sales_invoice(invoice_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await sales_invoice_crud.get(db, invoice_id)
    if not obj:
        raise APIError(404, "INVOICE_NOT_FOUND", f"Sales invoice {invoice_id} not found")
    return success(InvoiceHeaderRead.model_validate(obj), "Sales invoice fetched successfully", request)


@router.post("/", response_model=Envelope[InvoiceHeaderRead], response_model_exclude_none=True, status_code=201)
async def create_sales_invoice(payload: InvoiceHeaderCreate, request: Request, db: AsyncSession = Depends(get_db)):
    if payload.sales_order_id is not None:
        so = await sales_order_crud.get(db, payload.sales_order_id)
        if not so:
            raise APIError(404, "SALES_ORDER_NOT_FOUND", f"Sales order {payload.sales_order_id} not found")
        if so.doc_state != 3:
            raise APIError(
                422,
                "SALES_ORDER_NOT_APPROVED",
                f"Sales order {payload.sales_order_id} must be approved/posted before creating a sales invoice",
            )
        existing_approved_pl = (await db.execute(
            select(PackingListHeader).where(
                PackingListHeader.sales_order_id == payload.sales_order_id,
                PackingListHeader.doc_state == 3
            )
        )).scalar_one_or_none()
        if not existing_approved_pl:
            raise APIError(
                422,
                "PACKING_LIST_NOT_APPROVED",
                f"Sales order {payload.sales_order_id} does not have an approved/posted packing list yet.",
            )
        existing_inv = (await db.execute(
            select(InvoiceHeader).where(
                InvoiceHeader.sales_order_id == payload.sales_order_id,
                InvoiceHeader.doc_state != 5
            )
        )).scalar_one_or_none()
        if existing_inv:
            raise APIError(
                409,
                "SALES_ORDER_ALREADY_INVOICED",
                f"Sales order {payload.sales_order_id} already has an associated sales invoice ({existing_inv.invoice_no})",
            )
    try:
        obj = await sales_invoice_crud.create(db, payload)
    except IntegrityError:
        await db.rollback()
        raise APIError(
            409,
            "SALES_ORDER_ALREADY_INVOICED",
            f"Sales order {payload.sales_order_id} already has an associated sales invoice",
        )
    except ValueError as e:
        raise APIError(422, "VALIDATION_ERROR", "Validation failed", [{"field": "sales_invoice", "message": str(e)}])
    return success(InvoiceHeaderRead.model_validate(obj), "Sales invoice created successfully", request)


@router.put("/{invoice_id}", response_model=Envelope[InvoiceHeaderRead], response_model_exclude_none=True)
async def update_sales_invoice(
    invoice_id: int,
    payload: InvoiceHeaderUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    obj = await sales_invoice_crud.get(db, invoice_id)
    if not obj:
        raise APIError(404, "INVOICE_NOT_FOUND", f"Sales invoice {invoice_id} not found")

    if obj.doc_state > 1:
        raise APIError(
            409,
            "DOCUMENT_STATE_LOCKED",
            "Cannot update sales invoice after it has progressed past 'New Entry'.",
        )

    if payload.sales_order_id is not None:
        so = await sales_order_crud.get(db, payload.sales_order_id)
        if not so:
            raise APIError(404, "SALES_ORDER_NOT_FOUND", f"Sales order {payload.sales_order_id} not found")
        if so.doc_state != 3:
            raise APIError(
                422,
                "SALES_ORDER_NOT_APPROVED",
                f"Sales order {payload.sales_order_id} must be approved before updating a sales invoice",
            )
        existing_approved_pl = (await db.execute(
            select(PackingListHeader).where(
                PackingListHeader.sales_order_id == payload.sales_order_id,
                PackingListHeader.doc_state == 3
            )
        )).scalar_one_or_none()
        if not existing_approved_pl:
            raise APIError(
                422,
                "PACKING_LIST_NOT_APPROVED",
                f"Sales order {payload.sales_order_id} does not have an posted packing list yet.",
            )
        if payload.sales_order_id != obj.sales_order_id:
            existing_inv = (await db.execute(
                select(InvoiceHeader).where(
                    InvoiceHeader.sales_order_id == payload.sales_order_id,
                    InvoiceHeader.doc_state != 5
                )
            )).scalar_one_or_none()
            if existing_inv:
                raise APIError(
                    409,
                    "SALES_ORDER_ALREADY_INVOICED",
                    f"Sales order {payload.sales_order_id} already has an associated sales invoice ({existing_inv.invoice_no})",
                )

    try:
        obj = await sales_invoice_crud.update(db, obj, payload)
    except IntegrityError:
        await db.rollback()
        raise APIError(
            409,
            "SALES_ORDER_ALREADY_INVOICED",
            f"Sales order {payload.sales_order_id} already has an associated sales invoice",
        )
    except ValueError as e:
        raise APIError(422, "VALIDATION_ERROR", "Validation failed", [{"field": "sales_invoice", "message": str(e)}])
    return success(InvoiceHeaderRead.model_validate(obj), "Sales invoice updated successfully", request)


@router.patch("/{invoice_id}/state", response_model=Envelope[InvoiceHeaderRead], response_model_exclude_none=True)
async def update_sales_invoice_state(
    invoice_id: int,
    body: StateUpdateIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    obj = await advance_invoice_state(db, invoice_id, body.to_seq)
    return success(InvoiceHeaderRead.model_validate(obj), "Sales invoice state updated successfully", request)


@router.delete("/{invoice_id}", status_code=204)
async def delete_sales_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    obj = await sales_invoice_crud.get(db, invoice_id)
    if not obj:
        raise APIError(404, "INVOICE_NOT_FOUND", f"Sales invoice {invoice_id} not found")

    if obj.doc_state > 1:
        raise APIError(
            409,
            "DOCUMENT_STATE_LOCKED",
            "Cannot delete sales invoice in state other than 'New Entry'.",
        )

    ok = await sales_invoice_crud.delete(db, invoice_id)
    if not ok:
        raise APIError(404, "INVOICE_NOT_FOUND", f"Sales invoice {invoice_id} not found")
