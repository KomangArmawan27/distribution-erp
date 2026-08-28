from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.core.base_crud import CRUDBase, PageResult
from app.modules.group.crud import populate_group_displays
from app.core.pagination import compute_page_result
from app.modules.group.models import Group
from app.modules.sales_order.models import OrderHeader, OrderDetail
from app.modules.sales_order.schemas import OrderHeaderCreate, OrderHeaderUpdate

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
