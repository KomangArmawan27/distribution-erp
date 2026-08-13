from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Group
from app.schemas.group import GroupCreate, GroupUpdate

group_crud = CRUDBase[Group, GroupCreate, GroupUpdate](Group)


async def get_group_value(db: AsyncSession, group_name: str, group_noid: int | None) -> str:
    if group_noid is None:
        return ""
    result = await db.execute(
        select(Group.group_value).where(Group.group_name == group_name, Group.group_noid == group_noid)
    )
    value = result.scalar_one_or_none()
    if value is None:
        raise ValueError(f"group '{group_name}' noid {group_noid} not found")
    return value