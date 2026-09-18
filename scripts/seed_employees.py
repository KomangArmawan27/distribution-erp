import asyncio
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.modules.employee.models import Employee

INITIAL_EMPLOYEES = [
    {
        "employee_no": "EMP001",
        "employee_name": "John Doe",
        "position": 1,  # MANAGER
        "department": 1,  # SALES
        "join_date": date(2023, 1, 15),
        "status": 1,  # ACTIVE
    },
    {
        "employee_no": "EMP002",
        "employee_name": "Jane Smith",
        "position": 2,  # STAFF
        "department": 2,  # IT
        "join_date": date(2023, 3, 10),
        "status": 1,  # ACTIVE
    },
    {
        "employee_no": "EMP003",
        "employee_name": "Bob Johnson",
        "position": 2,  # STAFF
        "department": 1,  # SALES
        "join_date": date(2023, 6, 1),
        "status": 1,  # ACTIVE
    },
]


async def seed():
    print("Starting employee database seeding...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for emp_data in INITIAL_EMPLOYEES:
                stmt = select(Employee).where(Employee.employee_no == emp_data["employee_no"])
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if not existing:
                    session.add(Employee(**emp_data))
                    print(f"  [+] Added Employee: {emp_data['employee_no']} - {emp_data['employee_name']}")
                else:
                    existing.employee_name = emp_data["employee_name"]
                    existing.position = emp_data["position"]
                    existing.department = emp_data["department"]
                    existing.join_date = emp_data["join_date"]
                    existing.status = emp_data["status"]
                    print(f"  [=] Updated Employee: {emp_data['employee_no']} - {emp_data['employee_name']}")
        await session.commit()
    print("Employee seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
