import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.seed_groups import seed as seed_groups_func
from scripts.seed_doctypes import seed as seed_doctypes_func
from scripts.seed_employees import seed as seed_employees_func
from scripts.seed_sales_persons import seed as seed_sales_persons_func
from scripts.seed_items import seed as seed_items_func
from scripts.seed_item_pricelists import seed as seed_item_pricelists_func
from scripts.seed_customers import seed as seed_customers_func


async def seed_all():
    print("========================================")
    print(" Running Master ERP Database Seeder     ")
    print("========================================")
    
    print("\n[1/7] Seeding System Groups & Lookups...")
    await seed_groups_func()
    
    print("\n[2/7] Seeding Document Types & Flow States...")
    await seed_doctypes_func()

    print("\n[3/7] Seeding Employees...")
    await seed_employees_func()

    print("\n[4/7] Seeding Sales Persons...")
    await seed_sales_persons_func()

    print("\n[5/7] Seeding Items...")
    await seed_items_func()

    print("\n[6/7] Seeding Item Pricelists...")
    await seed_item_pricelists_func()

    print("\n[7/7] Seeding Customers...")
    await seed_customers_func()
    
    print("\n========================================")
    print(" Master Seeding Completed Successfully! ")
    print("========================================")


if __name__ == "__main__":
    asyncio.run(seed_all())
