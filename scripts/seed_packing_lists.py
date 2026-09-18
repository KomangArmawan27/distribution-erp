import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.modules.packing_list.models import PackingListHeader, PackingListDetail
from app.modules.sales_order.models import OrderHeader
from app.modules.packing_list.crud import packing_list_crud, advance_packing_list_state
from app.modules.packing_list.schemas import PackingListHeaderCreate, PackingListDetailCreate


async def seed():
    print("Starting packing list database seeding...")
    async with AsyncSessionLocal() as session:
        # Get first sales order
        so = (await session.execute(
            select(OrderHeader).options(selectinload(OrderHeader.details)).limit(1)
        )).scalar_one_or_none()
        
        if not so:
            print("  [!] No sales order found. Please seed sales orders first.")
            return

        # 1. Valid Packing List (linked to sales order, matching items, advance through states)
        pl_data_valid = PackingListHeaderCreate(
            sales_order_id=so.doc_id,
            details=[PackingListDetailCreate(item_id=d.item_id, trans_qty=d.trans_qty) for d in so.details]
        )
        existing_valid = (await session.execute(
            select(PackingListHeader).where(PackingListHeader.sales_order_id == so.doc_id)
        )).scalar_one_or_none()

        if not existing_valid:
            valid_pl = await packing_list_crud.create(session, pl_data_valid)
            print(f"  [+] Created Valid Packing List: {valid_pl.packing_list_no} (Linked to Sales Order {so.doc_no})")
            try:
                await advance_packing_list_state(session, valid_pl.packing_list_id, 2)
                await advance_packing_list_state(session, valid_pl.packing_list_id, 3)
                print(f"  [+] Advanced Valid Packing List to state 3 (Approved) successfully!")
            except Exception as e:
                print(f"  [!] Failed to advance valid packing list: {e}")
        else:
            print(f"  [=] Valid Packing List already exists: {existing_valid.packing_list_no}")

        # 2. Packing List stuck at New Entry (sales_order_id = None)
        null_pl_stmt = select(PackingListHeader).where(PackingListHeader.sales_order_id.is_(None)).limit(1)
        existing_null = (await session.execute(null_pl_stmt)).scalar_one_or_none()

        if not existing_null:
            pl_data_null = PackingListHeaderCreate(
                sales_order_id=None,
                details=[PackingListDetailCreate(item_id=so.details[0].item_id, trans_qty=1)]
            )
            null_pl = await packing_list_crud.create(session, pl_data_null)
            print(f"  [+] Created Packing List (No Sales Order): {null_pl.packing_list_no}")
            try:
                await advance_packing_list_state(session, null_pl.packing_list_id, 2)
            except Exception as e:
                print(f"  [+] Guard 1 successfully blocked transition for null sales_order_id: {e}")
        else:
            print(f"  [=] Null-SO Packing List already exists: {existing_null.packing_list_no}")

    print("Packing list seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
