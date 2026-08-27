import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.config.database import AsyncSessionLocal
from app.models import Group

INITIAL_GROUPS = [
    # --- Item Master Groups ---
    ("SUB GROUP", 1, "FREEBASE"),
    ("SUB GROUP", 2, "SALTNIC"),
    ("BRAND GROUP", 1, "BLONDIES"),
    ("BRAND GROUP", 2, "LOCOZ"),
    ("BRAND GROUP", 3, "UNA"),
    ("SERIES GROUP", 1, "MASTERPIECE SERIES"),
    ("PACK GROUP", 1, "10 PCS"),
    ("ML GROUP", 1, "15 ML"),
    ("ML GROUP", 2, "30 ML"),
    ("ML GROUP", 3, "60 ML"),
    ("NIC GROUP", 1, "3 MG"),
    ("NIC GROUP", 2, "6 MG"),

    # --- Employee Groups ---
    ("EMPLOYEE POSITION", 1, "MANAGER"),
    ("EMPLOYEE POSITION", 2, "STAFF"),
    ("EMPLOYEE POSITION", 3, "DIRECTOR"),
    ("EMPLOYEE DEPARTMENT", 1, "SALES"),
    ("EMPLOYEE DEPARTMENT", 2, "IT"),
    ("EMPLOYEE DEPARTMENT", 3, "FINANCE"),
    ("EMPLOYEE STATUS", 1, "ACTIVE"),
    ("EMPLOYEE STATUS", 2, "RESIGNED"),
    ("EMPLOYEE STATUS", 3, "SUSPENDED"),

    # --- Customer Groups ---
    ("CUSTOMER TYPE", 1, "RETAIL"),
    ("CUSTOMER TYPE", 2, "WHOLESALE"),
    ("CUSTOMER TYPE", 3, "DISTRIBUTOR"),
    ("CUSTOMER REGION", 1, "NORTH"),
    ("CUSTOMER REGION", 2, "SOUTH"),
    ("CUSTOMER REGION", 3, "CENTRAL"),
    ("CUSTOMER STATUS", 1, "ACTIVE"),
    ("CUSTOMER STATUS", 2, "INACTIVE"),

    # --- Sales Person Groups ---
    ("SALES AREA", 1, "JAKARTA"),
    ("SALES AREA", 2, "SURABAYA"),
    ("SALES AREA", 3, "BANDUNG"),
    ("SALES LEVEL", 1, "JUNIOR"),
    ("SALES LEVEL", 2, "SENIOR"),
    ("SALES LEVEL", 3, "LEAD"),
]


async def seed():
    print("Starting system group database seeding...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for g_name, g_noid, g_val in INITIAL_GROUPS:
                stmt = select(Group).where(Group.group_name == g_name, Group.group_noid == g_noid)
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if not existing:
                    session.add(Group(group_name=g_name, group_noid=g_noid, group_value=g_val))
                    print(f"  [+] Added: {g_name} [{g_noid}] -> {g_val}")
                else:
                    print(f"  [=] Exists: {g_name} [{g_noid}] -> {existing.group_value}")
        await session.commit()
    print("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
