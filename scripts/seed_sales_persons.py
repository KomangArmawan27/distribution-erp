import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.modules.employee.models import Employee
from app.modules.sales_person.models import SalesPerson

INITIAL_SALES_PERSONS = [
    {
        "sales_person_no": "SP001",
        "employee_no": "EMP001",
        "sales_area": 1,  # JAKARTA
        "sales_level": 3,  # LEAD
        "status": 1,  # ACTIVE
    },
    {
        "sales_person_no": "SP002",
        "employee_no": "EMP003",
        "sales_area": 2,  # SURABAYA
        "sales_level": 1,  # JUNIOR
        "status": 1,  # ACTIVE
    },
]


async def seed():
    print("Starting sales person database seeding...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for sp_data in INITIAL_SALES_PERSONS:
                emp_no = sp_data.pop("employee_no")
                emp = (await session.execute(select(Employee).where(Employee.employee_no == emp_no))).scalar_one_or_none()
                if not emp:
                    print(f"  [!] Employee {emp_no} not found for sales person {sp_data['sales_person_no']}, skipping.")
                    continue
                sp_data["employee_id"] = emp.employee_id

                stmt = select(SalesPerson).where(SalesPerson.sales_person_no == sp_data["sales_person_no"])
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if not existing:
                    session.add(SalesPerson(**sp_data))
                    print(f"  [+] Added Sales Person: {sp_data['sales_person_no']} (Employee: {emp_no})")
                else:
                    existing.employee_id = sp_data["employee_id"]
                    existing.sales_area = sp_data["sales_area"]
                    existing.sales_level = sp_data["sales_level"]
                    existing.status = sp_data["status"]
                    print(f"  [=] Updated Sales Person: {sp_data['sales_person_no']} (Employee: {emp_no})")
        await session.commit()
    print("Sales person seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
