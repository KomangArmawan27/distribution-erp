from datetime import date
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.core.base_crud import CRUDBase, PageResult
from app.modules.group.crud import populate_group_displays
from app.modules.system.crud import populate_flow_state_displays
from app.core.pagination import compute_page_result
from app.core.response import APIError
from app.modules.packing_list.models import PackingListHeader, PackingListDetail
from app.modules.packing_list.schemas import PackingListHeaderCreate, PackingListHeaderUpdate
from app.modules.sales_order.models import OrderHeader
from app.modules.system.crud import change_document_state


async def _generate_packing_list_no(db: AsyncSession, doc_date: date) -> str:
    yy = doc_date.strftime("%y")
    mm = doc_date.strftime("%m")
    prefix = f"PL{yy}{mm}"
    
    count = (
        await db.execute(
            select(func.count()).select_from(PackingListHeader).where(PackingListHeader.packing_list_no.like(f"{prefix}%"))
        )
    ).scalar() or 0
    return f"{prefix}{count + 1:04d}"


class CRUDPackingList(CRUDBase[PackingListHeader, PackingListHeaderCreate, PackingListHeaderUpdate]):
    async def get(self, db: AsyncSession, id_: int) -> PackingListHeader | None:
        stmt = select(self.model).options(
            selectinload(self.model.details).joinedload(PackingListDetail.item),
            joinedload(self.model.sales_order),
        ).where(self.pk_column == id_)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def page(
        self,
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        extra_filter=None,
    ) -> PageResult:
        pk = self.pk_column
        stmt = select(self.model).options(
            selectinload(self.model.details).joinedload(PackingListDetail.item),
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

        return compute_page_result(list(rows), page, per_page, total_items, total_pages)

    async def create(self, db: AsyncSession, obj_in: PackingListHeaderCreate) -> PackingListHeader:
        data = obj_in.model_dump()
        details_data = data.pop("details")
        
        if not data.get("doc_date"):
            data["doc_date"] = date.today()
        
        doc_date = data["doc_date"]
        data["packing_list_no"] = await _generate_packing_list_no(db, doc_date)
        data["doctype_id"] = 2
        data["doc_state"] = 1  # New Entry

        header = PackingListHeader(**data)
        db.add(header)
        await db.flush()

        for idx, det in enumerate(details_data, start=1):
            detail = PackingListDetail(
                packing_list_id=header.packing_list_id,
                trans_idx=idx,
                item_id=det["item_id"],
                trans_qty=det["trans_qty"],
            )
            db.add(detail)

        await db.commit()
        await db.refresh(header)
        return await self.get(db, header.packing_list_id)

    async def update(self, db: AsyncSession, db_obj: PackingListHeader, obj_in: PackingListHeaderUpdate) -> PackingListHeader:
        data = obj_in.model_dump(exclude_unset=True)
        details_data = data.pop("details", None)

        for field, value in data.items():
            setattr(db_obj, field, value)

        if details_data is not None:
            for det in list(db_obj.details):
                await db.delete(det)
            
            for idx, det in enumerate(details_data, start=1):
                detail = PackingListDetail(
                    packing_list_id=db_obj.packing_list_id,
                    trans_idx=idx,
                    item_id=det["item_id"],
                    trans_qty=det["trans_qty"],
                )
                db.add(detail)

        await db.commit()
        await db.refresh(db_obj)
        return await self.get(db, db_obj.packing_list_id)


packing_list_crud = CRUDPackingList(PackingListHeader)


async def advance_packing_list_state(
    db: AsyncSession,
    packing_list_id: int,
    to_seq: int,
) -> PackingListHeader:
    header = await packing_list_crud.get(db, packing_list_id)
    if not header:
        raise APIError(404, "PACKING_LIST_NOT_FOUND", f"Packing list {packing_list_id} not found")

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
                pl_item_ids = {d.item_id for d in header.details}
                if order_item_ids != pl_item_ids:
                    missing = order_item_ids - pl_item_ids
                    extra = pl_item_ids - order_item_ids
                    raise APIError(
                        422,
                        "ITEM_MISMATCH",
                        f"Item mismatch with linked sales order. Missing items: {list(missing)}, Extra items: {list(extra)}",
                    )

    await change_document_state(
        db,
        doctype_id=2,
        doc_id=packing_list_id,
        to_seq=to_seq,
        current_user=None,
        model_cls=PackingListHeader,
    )
    return await packing_list_crud.get(db, packing_list_id)
