import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.modules.sales_person.models import SalesPerson
from app.modules.customer.models import Customer

INITIAL_CUSTOMERS = [
    {
        "customer_no": "CUST001",
        "customer_name": "PT Maju Jaya",
        "customer_type": 1,  # RETAIL
        "customer_top": 3,  # NET 15
        "sales_person_no": "SP001",
        "address": "Jl. Sudirman No. 123, Jakarta",
        "city_region": 1,  # NORTH
        "phone": "0215551234",
        "status": 1,  # ACTIVE
    },
    {
        "customer_no": "CUST002",
        "customer_name": "CV Berkah Abadi",
        "customer_type": 2,  # WHOLESALE
        "customer_top": 4,  # NET 30
        "sales_person_no": "SP002",
        "address": "Jl. Pemuda No. 45, Surabaya",
        "city_region": 2,  # SOUTH
        "phone": "0318889999",
        "status": 1,  # ACTIVE
    },
]


async def seed():
    print("Starting customer database seeding...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for cust_data in INITIAL_CUSTOMERS:
                sp_no = cust_data.pop("sales_person_no", None)
                sales_person_id = None
                if sp_no:
                    sp = (await session.execute(select(SalesPerson).where(SalesPerson.sales_person_no == sp_no))).scalar_one_or_none()
                    if sp:
                        sales_person_id = sp.sales_person_id
                cust_data["sales_person_id"] = sales_person_id

                stmt = select(Customer).where(Customer.customer_no == cust_data["customer_no"])
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if not existing:
                    session.add(Customer(**cust_data))
                    print(f"  [+] Added Customer: {cust_data['customer_no']} - {cust_data['customer_name']}")
                else:
                    existing.customer_name = cust_data["customer_name"]
                    existing.customer_type = cust_data["customer_type"]
                    existing.customer_top = cust_data["customer_top"]
                    existing.sales_person_id = cust_data["sales_person_id"]
                    existing.address = cust_data["address"]
                    existing.city_region = cust_data["city_region"]
                    existing.phone = cust_data["phone"]
                    existing.status = cust_data["status"]
                    print(f"  [=] Updated Customer: {cust_data['customer_no']} - {cust_data['customer_name']}")
        await session.commit()
    print("Customer seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
