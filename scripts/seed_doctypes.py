import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.modules.system.models import DocumentType, FlowState, FlowTransition

INITIAL_DOCUMENT_TYPES = [
    (1, "SALES_ORDER", "Sales Order"),
]

INITIAL_FLOW_STATES = [
    (1, 1, "New Entry"),
    (1, 2, "Documented"),
    (1, 3, "Approved"),
    (1, 4, "Rejected"),
]

INITIAL_FLOW_TRANSITIONS = [
    (1, 1, 2, "Submit / Document", 1),
    (1, 2, 3, "Approve", 1),
    (1, 2, 4, "Reject", 1),
    (1, 4, 1, "Reopen / Reset", 1),
]


async def seed():
    print("Starting document types & flow states database seeding...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. Seed Document Types
            for dt_id, dt_code, dt_name in INITIAL_DOCUMENT_TYPES:
                stmt = select(DocumentType).where(DocumentType.doctype_id == dt_id)
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if not existing:
                    session.add(DocumentType(doctype_id=dt_id, doctype_code=dt_code, doctype_name=dt_name))
                    print(f"  [+] Added DocumentType: {dt_code} (ID: {dt_id})")
                else:
                    existing.doctype_code = dt_code
                    existing.doctype_name = dt_name
                    print(f"  [=] Updated/Exists DocumentType: {dt_code} (ID: {dt_id})")

            # 2. Seed Flow States
            for dt_id, seq, state_label in INITIAL_FLOW_STATES:
                stmt = select(FlowState).where(FlowState.doctype_id == dt_id, FlowState.docflow_seq == seq)
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if not existing:
                    session.add(FlowState(doctype_id=dt_id, docflow_seq=seq, flow_state=state_label))
                    print(f"  [+] Added FlowState: DocType {dt_id}, Seq {seq} -> {state_label}")
                else:
                    existing.flow_state = state_label
                    print(f"  [=] Updated/Exists FlowState: DocType {dt_id}, Seq {seq} -> {state_label}")

            # 3. Seed Flow Transitions
            for dt_id, f_seq, t_seq, action, min_role in INITIAL_FLOW_TRANSITIONS:
                stmt = select(FlowTransition).where(
                    FlowTransition.doctype_id == dt_id,
                    FlowTransition.from_seq == f_seq,
                    FlowTransition.to_seq == t_seq,
                )
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if not existing:
                    session.add(
                        FlowTransition(
                            doctype_id=dt_id,
                            from_seq=f_seq,
                            to_seq=t_seq,
                            action_label=action,
                            min_role=min_role,
                        )
                    )
                    print(f"  [+] Added FlowTransition: DocType {dt_id} [{f_seq} -> {t_seq}] ({action})")
                else:
                    existing.action_label = action
                    existing.min_role = min_role
                    print(f"  [=] Updated/Exists FlowTransition: DocType {dt_id} [{f_seq} -> {t_seq}] ({action})")

        await session.commit()
    print("Document types & flow states database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
