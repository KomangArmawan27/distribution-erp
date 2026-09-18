import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.modules.item.models import Item
from app.modules.item.schemas import ItemCreate
from app.modules.item.crud import item_crud

INITIAL_ITEMS = [
    {
        "item_no": "ITM001",
        "sub_group": 1,  # FREEBASE
        "brand_group": 1,  # BLONDIES
        "series_group": 1,  # MASTERPIECE SERIES
        "flavour_group": "STRAWBERRY CUSTARD",
        "pack_group": 1,  # 10 PCS
        "ml_group": 3,  # 60 ML
        "nic_group": 1,  # 3 MG
        "item_year": 2026,
    },
    {
        "item_no": "ITM002",
        "sub_group": 2,  # SALTNIC
        "brand_group": 2,  # LOCOZ
        "series_group": 1,  # MASTERPIECE SERIES
        "flavour_group": "MANGO ICE",
        "pack_group": 1,  # 10 PCS
        "ml_group": 2,  # 30 ML
        "nic_group": 2,  # 6 MG
        "item_year": 2026,
    },
    {
        "item_no": "ITM003",
        "sub_group": 1,  # FREEBASE
        "brand_group": 3,  # UNA
        "series_group": 1,  # MASTERPIECE SERIES
        "flavour_group": "CREAMY TOBACCO",
        "pack_group": 1,  # 10 PCS
        "ml_group": 3,  # 60 ML
        "nic_group": 1,  # 3 MG
        "item_year": 2026,
    },
]


async def seed():
    print("Starting item database seeding with rule-based item_name generation...")
    async with AsyncSessionLocal() as session:
        for item_data in INITIAL_ITEMS:
            stmt = select(Item).where(Item.item_no == item_data["item_no"])
            existing = (await session.execute(stmt)).scalar_one_or_none()
            payload = ItemCreate(**item_data)
            if not existing:
                created = await item_crud.create(session, payload)
                print(f"  [+] Added Item: {created.item_no} - {created.item_name}")
            else:
                updated = await item_crud.update(session, existing, payload)
                print(f"  [=] Updated Item: {updated.item_no} - {updated.item_name}")
    print("Item seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
