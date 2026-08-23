from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase, PageResult, compute_page_result
from app.models import ItemPriceList
from app.schemas.item_pricelist import ItemPriceListCreate, ItemPriceListUpdate


class ItemPriceListCRUD(CRUDBase[ItemPriceList, ItemPriceListCreate, ItemPriceListUpdate]):
    async def get(self, db: AsyncSession, id_: int) -> ItemPriceList | None:
        stmt = select(self.model).options(joinedload(self.model.item)).where(self.pk_column == id_)
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
        stmt = select(self.model).options(joinedload(self.model.item))
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
        rows = (await db.execute(stmt.order_by(pk.desc()).offset(offset).limit(per_page))).scalars().unique().all()

        return compute_page_result(list(rows), page, per_page, total_items, total_pages)

    async def create(self, db: AsyncSession, obj_in: ItemPriceListCreate) -> ItemPriceList:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        return await self.get(db, db_obj.pricelist_id)

    async def update(self, db: AsyncSession, db_obj: ItemPriceList, obj_in: ItemPriceListUpdate) -> ItemPriceList:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        await db.commit()
        return await self.get(db, db_obj.pricelist_id)


item_pricelist_crud = ItemPriceListCRUD(ItemPriceList)