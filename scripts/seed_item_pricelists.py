import asyncio
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.modules.item.models import Item
from app.modules.item_pricelist.models import ItemPriceList

INITIAL_PRICELISTS = [
    {
        "item_no": "ITM001",
        "item_price_ms": Decimal("150000.00"),
        "item_price_ws": Decimal("120000.00"),
        "item_price_distri": Decimal("100000.00"),
    },
    {
        "item_no": "ITM002",
        "item_price_ms": Decimal("100000.00"),
        "item_price_ws": Decimal("80000.00"),
        "item_price_distri": Decimal("70000.00"),
    },
    {
        "item_no": "ITM003",
        "item_price_ms": Decimal("200000.00"),
        "item_price_ws": Decimal("160000.00"),
        "item_price_distri": Decimal("140000.00"),
    },
]


async def seed():
    print("Starting item pricelist database seeding...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for pl_data in INITIAL_PRICELISTS:
                item_no = pl_data.pop("item_no")
                item = (await session.execute(select(Item).where(Item.item_no == item_no))).scalar_one_or_none()
                if not item:
                    print(f"  [!] Item {item_no} not found for pricelist, skipping.")
                    continue
                pl_data["item_id"] = item.item_id

                stmt = select(ItemPriceList).where(ItemPriceList.item_id == item.item_id)
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if not existing:
                    session.add(ItemPriceList(**pl_data))
                    print(f"  [+] Added Pricelist for Item: {item_no}")
                else:
                    existing.item_price_ms = pl_data["item_price_ms"]
                    existing.item_price_ws = pl_data["item_price_ws"]
                    existing.item_price_distri = pl_data["item_price_distri"]
                    print(f"  [=] Updated Pricelist for Item: {item_no}")
        await session.commit()
    print("Item pricelist seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
