from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase, PageResult
from app.crud.group import populate_group_displays
from app.models import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate

EMPLOYEE_GROUP_MAPPING = {
    "position": "EMPLOYEE POSITION",
    "department": "EMPLOYEE DEPARTMENT",
    "status": "EMPLOYEE STATUS",
}


class CRUDEmployee(CRUDBase[Employee, EmployeeCreate, EmployeeUpdate]):
    async def get(self, db: AsyncSession, id_: int) -> Employee | None:
        obj = await super().get(db, id_)
        if obj:
            await populate_group_displays(db, [obj], EMPLOYEE_GROUP_MAPPING)
        return obj

    async def page(
        self,
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        extra_filter=None,
    ) -> PageResult:
        page_result = await super().page(db, page=page, per_page=per_page, extra_filter=extra_filter)
        await populate_group_displays(db, page_result.items, EMPLOYEE_GROUP_MAPPING)
        return page_result

    async def create(self, db: AsyncSession, obj_in: EmployeeCreate) -> Employee:
        data = obj_in.model_dump()
        if not data.get("employee_no"):
            count = (await db.execute(select(func.count()).select_from(Employee))).scalar() or 0
            data["employee_no"] = f"EMP{count + 1:04d}"
        db_obj = Employee(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        await populate_group_displays(db, [db_obj], EMPLOYEE_GROUP_MAPPING)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: Employee, obj_in: EmployeeUpdate) -> Employee:
        obj = await super().update(db, db_obj, obj_in)
        await populate_group_displays(db, [obj], EMPLOYEE_GROUP_MAPPING)
        return obj


employee_crud = CRUDEmployee(Employee)
