from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase, PageResult
from app.crud.group import populate_group_displays
from app.models import SalesPerson
from app.schemas.sales_person import SalesPersonCreate, SalesPersonUpdate

SALES_PERSON_GROUP_MAPPING = {
    "sales_area": "SALES AREA",
    "sales_level": "SALES LEVEL",
    "status": "EMPLOYEE STATUS",
}


class CRUDSalesPerson(CRUDBase[SalesPerson, SalesPersonCreate, SalesPersonUpdate]):
    async def get(self, db: AsyncSession, id_: int) -> SalesPerson | None:
        obj = await super().get(db, id_)
        if obj:
            await populate_group_displays(db, [obj], SALES_PERSON_GROUP_MAPPING)
        return obj

    async def page(
        self,
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        extra_filter=None,
    ) -> PageResult:
        page_result = await super().page(db, page=page, per_page=per_page, extra_filter=extra_filter)
        await populate_group_displays(db, page_result.items, SALES_PERSON_GROUP_MAPPING)
        return page_result

    async def create(self, db: AsyncSession, obj_in: SalesPersonCreate) -> SalesPerson:
        data = obj_in.model_dump()
        if not data.get("sales_person_no"):
            count = (await db.execute(select(func.count()).select_from(SalesPerson))).scalar() or 0
            data["sales_person_no"] = f"SP{count + 1:04d}"
        db_obj = SalesPerson(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        await populate_group_displays(db, [db_obj], SALES_PERSON_GROUP_MAPPING)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: SalesPerson, obj_in: SalesPersonUpdate) -> SalesPerson:
        obj = await super().update(db, db_obj, obj_in)
        await populate_group_displays(db, [obj], SALES_PERSON_GROUP_MAPPING)
        return obj


sales_person_crud = CRUDSalesPerson(SalesPerson)
