from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.crud.group import get_group_value
from app.models import Group, Item
from app.schemas.item import ItemCreate, ItemUpdate

# field name -> group_name used to resolve each *_group column
GROUP_LOOKUPS = {
    "sub_group": "SUB GROUP",
    "brand_group": "BRAND GROUP",
    "series_group": "SERIES GROUP",
    "pack_group": "PACK GROUP",
    "ml_group": "ML GROUP",
    "nic_group": "NIC GROUP",
}
# order used to derive item_name
NAME_ORDER = ["sub_group", "brand_group", "series_group", "flavour_group", "pack_group", "ml_group", "nic_group"]

_LOOKUP_NAMES = {GROUP_LOOKUPS[f]: f for f in GROUP_LOOKUPS}


async def _generate_item_no(db: AsyncSession, flavour_group: str | None) -> str:
    if not flavour_group:
        raise ValueError("item_no and flavour_group are both missing; cannot generate item_no")
    prefix = flavour_group.strip().upper()[:3]
    if not prefix:
        raise ValueError("flavour_group is empty; cannot generate item_no")

    count = (
        await db.execute(
            select(func.count()).select_from(Item).where(func.coalesce(func.upper(Item.flavour_group), "") == flavour_group.strip().upper())
        )
    ).scalar() or 0
    return f"{prefix}{count + 1:04d}"


async def _build_item_name(db: AsyncSession, values: dict) -> str:
    parts: list[str] = []
    noids = {GROUP_LOOKUPS[f]: values.get(f) for f in GROUP_LOOKUPS if values.get(f) is not None}
    rows = (
        await db.execute(select(Group.group_name, Group.group_noid, Group.group_value).where(Group.group_name.in_(noids)))
    ).all()
    lookup = {(g.group_name, g.group_noid): g.group_value for g in rows}
    for field in NAME_ORDER:
        if field not in GROUP_LOOKUPS:
            part = values.get(field)
        else:
            noid = values.get(field)
            if noid is None:
                continue
            part = lookup.get((GROUP_LOOKUPS[field], noid))
            if part is None:
                raise ValueError(f"group '{GROUP_LOOKUPS[field]}' noid {noid} not found")
        if part:
            parts.append(str(part))
    if not parts:
        raise ValueError("at least one component is required to derive item_name")
    return " ".join(parts)


class CRUDItem(CRUDBase[Item, ItemCreate, ItemUpdate]):
    async def create(self, db: AsyncSession, obj_in: ItemCreate) -> Item:
        data = obj_in.model_dump()
        if not data.get("item_no"):
            data["item_no"] = await _generate_item_no(db, data.get("flavour_group"))
        data["item_name"] = await _build_item_name(db, data)
        db_obj = Item(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: Item, obj_in: ItemUpdate) -> Item:
        data = obj_in.model_dump(exclude_unset=True)
        merged = {c.name: getattr(db_obj, c.name) for c in db_obj.__table__.columns}
        merged.update(data)
        data["item_name"] = await _build_item_name(db, merged)
        for field, value in data.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


item_crud = CRUDItem(Item)