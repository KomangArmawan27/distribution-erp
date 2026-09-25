from datetime import date
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.core.base_crud import CRUDBase, PageResult
from app.core.pagination import compute_page_result
from app.core.response import APIError
from app.modules.sales_invoice.models import InvoiceHeader, InvoiceDetail
from app.modules.sales_invoice.schemas import InvoiceHeaderCreate, InvoiceHeaderUpdate
from app.modules.sales_order.models import OrderHeader
from app.modules.customer.models import Customer
from app.modules.item_pricelist.models import ItemPriceList
from app.modules.system.crud import change_document_state, populate_flow_state_displays


async def _generate_invoice_no(db: AsyncSession, doc_date: date) -> str:
    yy = doc_date.strftime("%y")
    mm = doc_date.strftime("%m")
    prefix = f"INV{yy}{mm}"
    
    count = (
        await db.execute(
            select(func.count()).select_from(InvoiceHeader).where(InvoiceHeader.invoice_no.like(f"{prefix}%"))
        )
    ).scalar() or 0
    return f"{prefix}{count + 1:04d}"


_CUSTOMER_TYPE_PRICE_COLUMN = {
    1: ItemPriceList.item_price_ms,       # RETAIL
    2: ItemPriceList.item_price_ws,       # WHOLESALE
    3: ItemPriceList.item_price_distri,   # DISTRIBUTOR
}


async def _get_customer_type_for_invoice(
    db: AsyncSession, sales_order_id: int | None, customer_id: int | None
) -> int:
    cust_id = customer_id
    if cust_id is None and sales_order_id is not None:
        so_res = await db.execute(
            select(OrderHeader.cust_id).where(OrderHeader.doc_id == sales_order_id)
        )
        cust_id = so_res.scalar_one_or_none()

    if cust_id is None:
        cust_res = await db.execute(select(Customer.customer_id).limit(1))
        cust_id = cust_res.scalar_one_or_none()
        if cust_id is None:
            raise ValueError("No customer found for pricing lookup")

    res = await db.execute(
        select(Customer.customer_type).where(Customer.customer_id == cust_id)
    )
    customer_type = res.scalar_one_or_none()
    if customer_type is None:
        raise ValueError(f"Customer not found for customer_id {cust_id}")
    return customer_type


async def _get_item_price(db: AsyncSession, item_id: int, customer_type: int) -> Decimal:
    price_column = _CUSTOMER_TYPE_PRICE_COLUMN.get(customer_type)
    if price_column is None:
        raise ValueError(f"Unrecognized customer_type {customer_type}")

    res = await db.execute(
        select(price_column).where(ItemPriceList.item_id == item_id)
    )
    price = res.scalar_one_or_none()
    if price is None:
        raise ValueError(f"Pricelist not found for item_id {item_id}")
    return price


class CRUDInvoice(CRUDBase[InvoiceHeader, InvoiceHeaderCreate, InvoiceHeaderUpdate]):
    async def get(self, db: AsyncSession, id_: int) -> InvoiceHeader | None:
        stmt = select(self.model).options(
            selectinload(self.model.details).joinedload(InvoiceDetail.item),
            joinedload(self.model.sales_order),
        ).where(self.pk_column == id_)
        result = await db.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj:
            await populate_flow_state_displays(db, [obj])
        return obj

    async def page(
        self,
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        extra_filter=None,
    ) -> PageResult:
        pk = self.pk_column
        stmt = select(self.model).options(
            selectinload(self.model.details).joinedload(InvoiceDetail.item),
            joinedload(self.model.sales_order),
        )
        count_stmt = select(func.count()).select_from(self.model)
        if extra_filter is not None:
            stmt = stmt.where(extra_filter)
            count_stmt = count_stmt.where(extra_filter)

        total_items = (await db.execute(count_stmt)).scalar() or 0
        total_pages = max((total_items + per_page - 1) // per_page, 0) if per_page else 0

        if page > total_pages and total_pages > 0:
            page = total_pages
        if page < 1:
            page = 1

        offset = (page - 1) * per_page
        rows = (await db.execute(stmt.order_by(pk.desc()).offset(offset).limit(per_page))).unique().scalars().all()

        page_result = compute_page_result(list(rows), page, per_page, total_items, total_pages)
        await populate_flow_state_displays(db, page_result.items)
        return page_result

    async def create(self, db: AsyncSession, obj_in: InvoiceHeaderCreate) -> InvoiceHeader:
        data = obj_in.model_dump()
        details_data = data.pop("details")
        customer_id = data.pop("customer_id", None)

        customer_type = await _get_customer_type_for_invoice(
            db, data.get("sales_order_id"), customer_id
        )
        
        if not data.get("doc_date"):
            data["doc_date"] = date.today()
        
        doc_date = data["doc_date"]
        data["invoice_no"] = await _generate_invoice_no(db, doc_date)
        data["doctype_id"] = 3
        data["doc_state"] = 1  # New Entry

        header = InvoiceHeader(**data)
        db.add(header)
        await db.flush()

        for idx, det in enumerate(details_data, start=1):
            qty = det["trans_qty"]
            item_id = det["item_id"]
            price = await _get_item_price(db, item_id, customer_type)
            total = Decimal(str(qty)) * price
            detail = InvoiceDetail(
                invoice_id=header.invoice_id,
                trans_idx=idx,
                item_id=item_id,
                trans_qty=qty,
                item_price=price,
                trans_total=total,
            )
            db.add(detail)

        await db.commit()
        await db.refresh(header)
        return await self.get(db, header.invoice_id)

    async def update(self, db: AsyncSession, db_obj: InvoiceHeader, obj_in: InvoiceHeaderUpdate) -> InvoiceHeader:
        data = obj_in.model_dump(exclude_unset=True)
        details_data = data.pop("details", None)
        customer_id = data.pop("customer_id", None)

        effective_so_id = data.get("sales_order_id", db_obj.sales_order_id)
        customer_type = await _get_customer_type_for_invoice(
            db, effective_so_id, customer_id
        )

        for field, value in data.items():
            setattr(db_obj, field, value)

        if details_data is not None:
            for det in list(db_obj.details):
                await db.delete(det)
            
            for idx, det in enumerate(details_data, start=1):
                qty = det["trans_qty"]
                item_id = det["item_id"]
                price = await _get_item_price(db, item_id, customer_type)
                total = Decimal(str(qty)) * price
                detail = InvoiceDetail(
                    invoice_id=db_obj.invoice_id,
                    trans_idx=idx,
                    item_id=item_id,
                    trans_qty=qty,
                    item_price=price,
                    trans_total=total,
                )
                db.add(detail)

        await db.commit()
        await db.refresh(db_obj)
        return await self.get(db, db_obj.invoice_id)


sales_invoice_crud = CRUDInvoice(InvoiceHeader)


async def advance_invoice_state(
    db: AsyncSession,
    invoice_id: int,
    to_seq: int,
) -> InvoiceHeader:
    header = await sales_invoice_crud.get(db, invoice_id)
    if not header:
        raise APIError(404, "INVOICE_NOT_FOUND", f"Sales invoice {invoice_id} not found")

    # Guard 1: Leaving state 1 (New Entry) -> sales_order_id must not be None
    if header.doc_state == 1 and to_seq > 1:
        if header.sales_order_id is None:
            raise APIError(
                422,
                "TRANSITION_BLOCKED",
                "sales_order_id is null; link a sales order before proceeding past 'New Entry'",
            )

    # Guard 2: Leaving state 2 (Documented) -> item set must exactly match linked sales order
    if header.doc_state == 2 and to_seq > 2:
        if header.sales_order_id is not None:
            so_stmt = select(OrderHeader).options(selectinload(OrderHeader.details)).where(OrderHeader.doc_id == header.sales_order_id)
            so = (await db.execute(so_stmt)).scalar_one_or_none()
            if so:
                order_item_ids = {d.item_id for d in so.details}
                inv_item_ids = {d.item_id for d in header.details}
                if order_item_ids != inv_item_ids:
                    missing = order_item_ids - inv_item_ids
                    extra = inv_item_ids - order_item_ids
                    raise APIError(
                        422,
                        "ITEM_MISMATCH",
                        f"Item mismatch with linked sales order. Missing items: {list(missing)}, Extra items: {list(extra)}",
                    )


    await change_document_state(
        db,
        doctype_id=3,
        doc_id=invoice_id,
        to_seq=to_seq,
        current_user=None,
        model_cls=InvoiceHeader,
    )
    await db.commit()
    return await sales_invoice_crud.get(db, invoice_id)
