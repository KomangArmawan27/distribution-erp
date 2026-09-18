import asyncio
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.modules.sales_order.models import OrderHeader
from app.modules.sales_order.schemas import OrderHeaderCreate, OrderDetailCreate
from app.modules.sales_order.crud import sales_order_crud
from app.modules.customer.models import Customer
from app.modules.sales_person.models import SalesPerson
from app.modules.item.models import Item


async def seed():
    print("Starting sales order database seeding...")
    async with AsyncSessionLocal() as session:
        cust = (await session.execute(select(Customer).limit(1))).scalar_one_or_none()
        sp = (await session.execute(select(SalesPerson).limit(1))).scalar_one_or_none()
        item = (await session.execute(select(Item).limit(1))).scalar_one_or_none()

        if not cust or not sp or not item:
            print("  [!] Prerequisites (customer, sales person, item) not found. Please seed master data first.")
            return

        existing = (await session.execute(select(OrderHeader).limit(1))).scalar_one_or_none()
        if not existing:
            payload = OrderHeaderCreate(
                cust_id=cust.customer_id,
                doc_terms=3,  # NET 15
                sales_id=sp.sales_person_id,
                doc_date=date.today(),
                details=[
                    OrderDetailCreate(
                        item_id=item.item_id,
                        trans_qty=10,
                        trans_price=150000.00
                    )
                ]
            )
            so = await sales_order_crud.create(session, payload)
            print(f"  [+] Created Sales Order: {so.doc_no}")
        else:
            print(f"  [=] Sales order already exists: {existing.doc_no}")

    print("Sales order seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
