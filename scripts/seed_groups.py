import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.modules.group.models import Group

# (group_name, group_noid, group_display, group_value_int)
INITIAL_GROUPS = [
    # --- Item Master Groups ---
    ("SUB GROUP", 1, "FREEBASE", 0),
    ("SUB GROUP", 2, "SALTNIC", 0),
    ("BRAND GROUP", 1, "BLONDIES", 0),
    ("BRAND GROUP", 2, "LOCOZ", 0),
    ("BRAND GROUP", 3, "UNA", 0),
    ("SERIES GROUP", 1, "MASTERPIECE SERIES", 0),
    ("PACK GROUP", 1, "10 PCS", 10),
    ("ML GROUP", 1, "15 ML", 15),
    ("ML GROUP", 2, "30 ML", 30),
    ("ML GROUP", 3, "60 ML", 60),
    ("NIC GROUP", 1, "3 MG", 3),
    ("NIC GROUP", 2, "6 MG", 6),

    # --- Employee Groups ---
    ("EMPLOYEE POSITION", 1, "MANAGER", 0),
    ("EMPLOYEE POSITION", 2, "STAFF", 0),
    ("EMPLOYEE POSITION", 3, "DIRECTOR", 0),
    ("EMPLOYEE DEPARTMENT", 1, "SALES", 0),
    ("EMPLOYEE DEPARTMENT", 2, "IT", 0),
    ("EMPLOYEE DEPARTMENT", 3, "FINANCE", 0),
    ("EMPLOYEE STATUS", 1, "ACTIVE", 0),
    ("EMPLOYEE STATUS", 2, "RESIGNED", 0),
    ("EMPLOYEE STATUS", 3, "SUSPENDED", 0),

    # --- Customer Groups ---
    ("CUSTOMER TYPE", 1, "RETAIL", 0),
    ("CUSTOMER TYPE", 2, "WHOLESALE", 0),
    ("CUSTOMER TYPE", 3, "DISTRIBUTOR", 0),
    ("CUSTOMER REGION", 1, "NORTH", 0),
    ("CUSTOMER REGION", 2, "SOUTH", 0),
    ("CUSTOMER REGION", 3, "CENTRAL", 0),
    ("CUSTOMER STATUS", 1, "ACTIVE", 0),
    ("CUSTOMER STATUS", 2, "INACTIVE", 0),
    ("CUSTOMER TOP", 1, "COD", 0),
    ("CUSTOMER TOP", 2, "NET 7", 7),
    ("CUSTOMER TOP", 3, "NET 15", 15),
    ("CUSTOMER TOP", 4, "NET 30", 30),

    # --- Sales Person Groups ---
    ("SALES AREA", 1, "JAKARTA", 0),
    ("SALES AREA", 2, "SURABAYA", 0),
    ("SALES AREA", 3, "BANDUNG", 0),
    ("SALES LEVEL", 1, "JUNIOR", 0),
    ("SALES LEVEL", 2, "SENIOR", 0),
    ("SALES LEVEL", 3, "LEAD", 0),
]


async def seed():
    print("Starting system group database seeding...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for g_name, g_noid, g_display, g_val in INITIAL_GROUPS:
                stmt = select(Group).where(Group.group_name == g_name, Group.group_noid == g_noid)
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if not existing:
                    session.add(Group(group_name=g_name, group_noid=g_noid, group_display=g_display, group_value=g_val))
                    print(f"  [+] Added: {g_name} [{g_noid}] -> Display: {g_display}, Value: {g_val}")
                else:
                    # Update display & value if needed or keep
                    existing.group_display = g_display
                    existing.group_value = g_val
                    print(f"  [=] Updated/Exists: {g_name} [{g_noid}] -> Display: {g_display}, Value: {g_val}")
        await session.commit()
    print("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
