from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.core.base_crud import CRUDBase, PageResult
from app.modules.group.crud import populate_group_displays
from app.modules.system.crud import populate_flow_state_displays
from app.core.pagination import compute_page_result
from app.modules.group.models import Group
from app.modules.sales_order.models import OrderHeader, OrderDetail
from app.modules.sales_order.schemas import OrderHeaderCreate, OrderHeaderUpdate, OrderHeaderRead
from app.modules.packing_list.models import PackingListHeader
from app.modules.sales_invoice.models import InvoiceHeader
from app.modules.system.crud import change_document_state
from app.core.response import APIError

ORDER_HEADER_GROUP_MAPPING = {
    "doc_terms": "CUSTOMER TOP",
}


async def _generate_doc_no(db: AsyncSession, doc_date: date) -> str:
    yy = doc_date.strftime("%y")
    mm = doc_date.strftime("%m")
    prefix = f"SO{yy}{mm}"
    
    count = (
        await db.execute(
            select(func.count()).select_from(OrderHeader).where(OrderHeader.doc_no.like(f"{prefix}%"))
        )
    ).scalar() or 0
    return f"{prefix}{count + 1:04d}"


async def _get_doc_duedate(db: AsyncSession, doc_date: date, doc_terms: int) -> date:
    res = await db.execute(
        select(Group.group_value).where(Group.group_name == "CUSTOMER TOP", Group.group_noid == doc_terms)
    )
    days = res.scalar_one_or_none()
    if days is None:
        raise ValueError(f"CUSTOMER TOP term {doc_terms} not found")
    return doc_date + timedelta(days=days)


class CRUDSalesOrder(CRUDBase[OrderHeader, OrderHeaderCreate, OrderHeaderUpdate]):
    async def get(self, db: AsyncSession, id_: int) -> OrderHeader | None:
        stmt = select(self.model).options(
            selectinload(self.model.details).joinedload(OrderDetail.item)
        ).where(self.pk_column == id_)
        result = await db.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj:
            await populate_group_displays(db, [obj], ORDER_HEADER_GROUP_MAPPING)
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
            selectinload(self.model.details).joinedload(OrderDetail.item)
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
        await populate_group_displays(db, page_result.items, ORDER_HEADER_GROUP_MAPPING)
        await populate_flow_state_displays(db, page_result.items)
        return page_result

    async def create(self, db: AsyncSession, obj_in: OrderHeaderCreate) -> OrderHeader:
        data = obj_in.model_dump()
        details_data = data.pop("details")
        
        if not data.get("doc_date"):
            data["doc_date"] = date.today()
        
        doc_date = data["doc_date"]
        doc_terms = data["doc_terms"]
        
        data["doc_no"] = await _generate_doc_no(db, doc_date)
        data["doc_duedate"] = await _get_doc_duedate(db, doc_date, doc_terms)
        data["doctype_id"] = 1
        data["doc_state"] = 1  # Default New Entry
        
        header = OrderHeader(**data)
        db.add(header)
        await db.flush()

        for idx, det in enumerate(details_data, start=1):
            qty = det["trans_qty"]
            price = det["trans_price"]
            total = Decimal(str(qty)) * price
            detail = OrderDetail(
                doc_id=header.doc_id,
                trans_idx=idx,
                item_id=det["item_id"],
                trans_qty=qty,
                trans_price=price,
                trans_total=total,
            )
            db.add(detail)

        await db.commit()
        await db.refresh(header)
        return await self.get(db, header.doc_id)

    async def update(self, db: AsyncSession, db_obj: OrderHeader, obj_in: OrderHeaderUpdate) -> OrderHeader:
        existing_pl = (await db.execute(
            select(PackingListHeader).where(
                PackingListHeader.sales_order_id == db_obj.doc_id,
                PackingListHeader.doc_state.not_in([4, 5])
            )
        )).scalar_one_or_none()
        if existing_pl:
            raise ValueError("Sales Order cannot be edited because a non-cancelled/rejected Packing List exists against it.")

        data = obj_in.model_dump(exclude_unset=True)
        details_data = data.pop("details", None)

        doc_date = data.get("doc_date", db_obj.doc_date)
        doc_terms = data.get("doc_terms", db_obj.doc_terms)
        
        if "doc_date" in data or "doc_terms" in data:
            data["doc_duedate"] = await _get_doc_duedate(db, doc_date, doc_terms)

        for field, value in data.items():
            setattr(db_obj, field, value)

        if details_data is not None:
            for det in list(db_obj.details):
                await db.delete(det)
            
            for idx, det in enumerate(details_data, start=1):
                qty = det["trans_qty"]
                price = det["trans_price"]
                total = Decimal(str(qty)) * price
                detail = OrderDetail(
                    doc_id=db_obj.doc_id,
                    trans_idx=idx,
                    item_id=det["item_id"],
                    trans_qty=qty,
                    trans_price=price,
                    trans_total=total,
                )
                db.add(detail)

        await db.commit()
        await db.refresh(db_obj)
        return await self.get(db, db_obj.doc_id)


sales_order_crud = CRUDSalesOrder(OrderHeader)


async def advance_sales_order_state(
    db: AsyncSession,
    doc_id: int,
    to_seq: int,
) -> OrderHeader:
    header = await sales_order_crud.get(db, doc_id)
    if not header:
        raise APIError(404, "SALES_ORDER_NOT_FOUND", f"Sales order {doc_id} not found")

    if to_seq == 5:
        pl_stmt = select(PackingListHeader).where(PackingListHeader.sales_order_id == doc_id, PackingListHeader.doc_state == 3)
        approved_pl = (await db.execute(pl_stmt)).scalars().first()
        if approved_pl:
            raise APIError(
                422,
                "TRANSITION_BLOCKED",
                f"Cannot cancel — Packing List {approved_pl.packing_list_no} is still approved/posted. Cancel it first.",
            )

        inv_stmt = select(InvoiceHeader).where(InvoiceHeader.sales_order_id == doc_id, InvoiceHeader.doc_state == 3)
        approved_inv = (await db.execute(inv_stmt)).scalars().first()
        if approved_inv:
            raise APIError(
                422,
                "TRANSITION_BLOCKED",
                f"Cannot cancel — Sales Invoice {approved_inv.invoice_no} is still approved/posted. Cancel it first.",
            )

    await change_document_state(
        db,
        doctype_id=1,
        doc_id=doc_id,
        to_seq=to_seq,
        current_user=None,
        model_cls=OrderHeader,
    )
    return await sales_order_crud.get(db, doc_id)


async def cancel_order_cascade(
    db: AsyncSession,
    sales_order_id: int,
    confirm: bool = False,
    preview: bool = True,
) -> dict:
    so = await sales_order_crud.get(db, sales_order_id)
    if not so:
        raise APIError(404, "SALES_ORDER_NOT_FOUND", f"Sales order {sales_order_id} not found")

    invs = (await db.execute(select(InvoiceHeader).where(InvoiceHeader.sales_order_id == sales_order_id))).scalars().all()
    pls = (await db.execute(select(PackingListHeader).where(PackingListHeader.sales_order_id == sales_order_id))).scalars().all()

    actions = []
    for inv in invs:
        if inv.doc_state in (4, 5):
            continue
        if inv.doc_state == 3:
            actions.append(f"Create credit note for Invoice {inv.invoice_no}")
            actions.append(f"Cancel Sales Invoice {inv.invoice_no}")
        else:
            actions.append(f"Reject Sales Invoice {inv.invoice_no}")

    for pl in pls:
        if pl.doc_state in (4, 5):
            continue
        if pl.doc_state == 3:
            actions.append(f"Create return for Packing List {pl.packing_list_no} (qty returning to stock)")
            actions.append(f"Cancel Packing List {pl.packing_list_no}")
        else:
            actions.append(f"Reject Packing List {pl.packing_list_no}")

    if so.doc_state not in (4, 5):
        actions.append(f"Cancel Sales Order {so.doc_no}")

    if preview or not confirm:
        return {
            "preview": True,
            "message": "Review cancellation summary before executing.",
            "actions": actions,
        }

    from app.modules.sales_invoice.crud import advance_invoice_state
    from app.modules.packing_list.crud import advance_packing_list_state

    for inv in invs:
        if inv.doc_state in (4, 5):
            continue
        if inv.doc_state == 3:
            await advance_invoice_state(db, inv.invoice_id, 5)
        else:
            await change_document_state(db, doctype_id=3, doc_id=inv.invoice_id, to_seq=4, current_user=None, model_cls=InvoiceHeader)

    for pl in pls:
        if pl.doc_state in (4, 5):
            continue
        if pl.doc_state == 3:
            await advance_packing_list_state(db, pl.packing_list_id, 5, confirm_return=True)
        else:
            await change_document_state(db, doctype_id=2, doc_id=pl.packing_list_id, to_seq=4, current_user=None, model_cls=PackingListHeader)

    if so.doc_state not in (4, 5):
        await advance_sales_order_state(db, sales_order_id, 5)

    await db.commit()
    updated_so = await sales_order_crud.get(db, sales_order_id)
    return {
        "preview": False,
        "message": "Cancel order cascade completed successfully.",
        "sales_order": OrderHeaderRead.model_validate(updated_so),
    }
