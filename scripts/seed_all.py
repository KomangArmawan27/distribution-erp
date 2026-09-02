import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.seed_groups import seed as seed_groups_func
from scripts.seed_doctypes import seed as seed_doctypes_func


async def seed_all():
    print("========================================")
    print(" Running Master ERP Database Seeder     ")
    print("========================================")
    
    print("\n[1/2] Seeding System Groups & Lookups...")
    await seed_groups_func()
    
    print("\n[2/2] Seeding Document Types & Flow States...")
    await seed_doctypes_func()
    
    print("\n========================================")
    print(" Master Seeding Completed Successfully! ")
    print("========================================")


if __name__ == "__main__":
    asyncio.run(seed_all())
