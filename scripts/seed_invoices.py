import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.modules.sales_invoice.models import InvoiceHeader
from app.modules.sales_order.models import OrderHeader
from app.modules.sales_invoice.crud import sales_invoice_crud, advance_invoice_state
from app.modules.sales_invoice.schemas import InvoiceHeaderCreate, InvoiceDetailCreate


async def seed():
    print("Starting sales invoice database seeding...")
    async with AsyncSessionLocal() as session:
        so = (await session.execute(
            select(OrderHeader).options(selectinload(OrderHeader.details)).limit(1)
        )).scalar_one_or_none()
        
        if not so:
            print("  [!] No sales order found. Please seed sales orders first.")
            return

        # 1. Valid Sales Invoice (linked to sales order, matching items, advance through states)
        existing_valid = (await session.execute(
            select(InvoiceHeader).where(InvoiceHeader.sales_order_id == so.doc_id)
        )).scalar_one_or_none()

        if not existing_valid:
            inv_data_valid = InvoiceHeaderCreate(
                sales_order_id=so.doc_id,
                details=[InvoiceDetailCreate(item_id=d.item_id, trans_qty=d.trans_qty) for d in so.details]
            )
            valid_inv = await sales_invoice_crud.create(session, inv_data_valid)
            print(f"  [+] Created Valid Sales Invoice: {valid_inv.invoice_no} (Linked to Sales Order {so.doc_no})")
            try:
                await advance_invoice_state(session, valid_inv.invoice_id, 2)
                await advance_invoice_state(session, valid_inv.invoice_id, 3)
                print(f"  [+] Advanced Valid Sales Invoice to state 3 (Approved) successfully!")
            except Exception as e:
                print(f"  [!] Failed to advance valid sales invoice: {e}")
        else:
            print(f"  [=] Valid Sales Invoice already exists: {existing_valid.invoice_no}")

        # 2. Sales Invoice stuck at New Entry (sales_order_id = None)
        null_inv_stmt = select(InvoiceHeader).where(InvoiceHeader.sales_order_id.is_(None)).limit(1)
        existing_null = (await session.execute(null_inv_stmt)).scalar_one_or_none()

        if not existing_null:
            inv_data_null = InvoiceHeaderCreate(
                sales_order_id=None,
                details=[InvoiceDetailCreate(item_id=so.details[0].item_id, trans_qty=1)]
            )
            null_inv = await sales_invoice_crud.create(session, inv_data_null)
            print(f"  [+] Created Sales Invoice (No Sales Order): {null_inv.invoice_no}")
            try:
                await advance_invoice_state(session, null_inv.invoice_id, 2)
            except Exception as e:
                print(f"  [+] Guard 1 successfully blocked transition for null sales_order_id: {e}")
        else:
            print(f"  [=] Null-SO Sales Invoice already exists: {existing_null.invoice_no}")

    print("Sales invoice seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
