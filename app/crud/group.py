from sqlalchemy import or_, select
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


async def populate_group_displays(db: AsyncSession, objects: list, mapping: dict[str, str]) -> None:
    if not objects:
        return
    pairs = set()
    for obj in objects:
        for attr, group_name in mapping.items():
            noid = getattr(obj, attr, None)
            if noid is not None:
                pairs.add((group_name, noid))

    if not pairs:
        for obj in objects:
            for attr in mapping:
                setattr(obj, f"{attr}_display", None)
        return

    conditions = [
        (Group.group_name == g_name) & (Group.group_noid == g_noid)
        for g_name, g_noid in pairs
    ]
    stmt = select(Group.group_name, Group.group_noid, Group.group_value).where(or_(*conditions))
    rows = (await db.execute(stmt)).all()
    lookup = {(r.group_name, r.group_noid): r.group_value for r in rows}

    for obj in objects:
        for attr, group_name in mapping.items():
            noid = getattr(obj, attr, None)
            display_val = lookup.get((group_name, noid)) if noid is not None else None
            setattr(obj, f"{attr}_display", display_val)