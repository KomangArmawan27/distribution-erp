from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase, PageResult
from app.crud.group import populate_group_displays
from app.models import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate

CUSTOMER_GROUP_MAPPING = {
    "customer_type": "CUSTOMER TYPE",
    "city_region": "CUSTOMER REGION",
    "status": "CUSTOMER STATUS",
}


class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    async def get(self, db: AsyncSession, id_: int) -> Customer | None:
        obj = await super().get(db, id_)
        if obj:
            await populate_group_displays(db, [obj], CUSTOMER_GROUP_MAPPING)
        return obj

    async def page(
        self,
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        extra_filter=None,
    ) -> PageResult:
        page_result = await super().page(db, page=page, per_page=per_page, extra_filter=extra_filter)
        await populate_group_displays(db, page_result.items, CUSTOMER_GROUP_MAPPING)
        return page_result

    async def create(self, db: AsyncSession, obj_in: CustomerCreate) -> Customer:
        data = obj_in.model_dump()
        if not data.get("customer_no"):
            count = (await db.execute(select(func.count()).select_from(Customer))).scalar() or 0
            data["customer_no"] = f"CUST{count + 1:04d}"
        db_obj = Customer(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        await populate_group_displays(db, [db_obj], CUSTOMER_GROUP_MAPPING)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: Customer, obj_in: CustomerUpdate) -> Customer:
        obj = await super().update(db, db_obj, obj_in)
        await populate_group_displays(db, [obj], CUSTOMER_GROUP_MAPPING)
        return obj


customer_crud = CRUDCustomer(Customer)
