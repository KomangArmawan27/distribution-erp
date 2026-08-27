from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase, PageResult
from app.crud.group import populate_group_displays
from app.models import Group, Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate

CUSTOMER_GROUP_MAPPING = {
    "customer_type": "CUSTOMER TYPE",
    "customer_top": "CUSTOMER TOP",
    "city_region": "CUSTOMER REGION",
    "status": "CUSTOMER STATUS",
}


async def find_missing_group(db: AsyncSession, values: dict) -> tuple[str, int] | None:
    noids = {CUSTOMER_GROUP_MAPPING[f]: values.get(f) for f in CUSTOMER_GROUP_MAPPING if values.get(f) is not None}
    if not noids:
        return None
    rows = (
        await db.execute(select(Group.group_name, Group.group_noid).where(Group.group_name.in_(noids)))
    ).all()
    existing = {(g.group_name, g.group_noid) for g in rows}
    for field, group_name in CUSTOMER_GROUP_MAPPING.items():
        noid = values.get(field)
        if noid is not None and (group_name, noid) not in existing:
            return (group_name, noid)
    return None


async def _generate_customer_no(db: AsyncSession, customer_name: str | None) -> str:
    if not customer_name:
        raise ValueError("customer_no and customer_name are both missing; cannot generate customer_no")
    prefix = customer_name.strip().upper()[:3]
    if not prefix:
        raise ValueError("customer_name is empty; cannot generate customer_no")

    count = (
        await db.execute(
            select(func.count()).select_from(Customer).where(func.upper(Customer.customer_no).like(f"{prefix}%"))
        )
    ).scalar() or 0
    return f"{prefix}{count + 1:04d}"


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
            data["customer_no"] = await _generate_customer_no(db, data.get("customer_name"))
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
