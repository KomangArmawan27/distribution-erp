from typing import Any
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import CRUDBase
from app.core.response import APIError
from app.modules.system.models import DocumentType, FlowState, FlowTransition
from app.modules.system.schemas import (
    DocumentTypeCreate,
    DocumentTypeUpdate,
    FlowStateCreate,
    FlowStateUpdate,
    FlowTransitionCreate,
    FlowTransitionUpdate,
)

document_type_crud = CRUDBase[DocumentType, DocumentTypeCreate, DocumentTypeUpdate](DocumentType)
flow_state_crud = CRUDBase[FlowState, FlowStateCreate, FlowStateUpdate](FlowState)
flow_transition_crud = CRUDBase[FlowTransition, FlowTransitionCreate, FlowTransitionUpdate](FlowTransition)


async def populate_flow_state_displays(
    db: AsyncSession,
    objects: list,
    state_attr: str = "doc_state",
    display_attr: str = "doc_state_display",
) -> None:
    if not objects:
        return
    pairs = set()
    for obj in objects:
        doctype_id = getattr(obj, "doctype_id", None)
        seq = getattr(obj, state_attr, None)
        if doctype_id is not None and seq is not None:
            pairs.add((doctype_id, seq))

    if not pairs:
        for obj in objects:
            setattr(obj, display_attr, None)
        return

    conditions = [
        (FlowState.doctype_id == dt_id) & (FlowState.docflow_seq == s)
        for dt_id, s in pairs
    ]
    stmt = select(FlowState.doctype_id, FlowState.docflow_seq, FlowState.flow_state).where(or_(*conditions))
    rows = (await db.execute(stmt)).all()
    lookup = {(r.doctype_id, r.docflow_seq): r.flow_state for r in rows}

    for obj in objects:
        doctype_id = getattr(obj, "doctype_id", None)
        seq = getattr(obj, state_attr, None)
        display_val = lookup.get((doctype_id, seq)) if doctype_id is not None and seq is not None else None
        setattr(obj, display_attr, display_val)


async def change_document_state(
    db: AsyncSession,
    doctype_id: int,
    doc_id: int,
    to_seq: int,
    current_user: Any,
    model_cls: type,
) -> Any:
    doc = await db.get(model_cls, doc_id)
    if doc is None:
        raise APIError(404, "DOCUMENT_NOT_FOUND", f"Document {doc_id} not found")

    stmt = select(FlowTransition).where(
        FlowTransition.doctype_id == doctype_id,
        FlowTransition.from_seq == doc.doc_state,
        FlowTransition.to_seq == to_seq,
    )
    transition = (await db.execute(stmt)).scalar_one_or_none()
    if transition is None:
        raise APIError(
            404,
            "TRANSITION_NOT_ALLOWED",
            f"Transition from state {doc.doc_state} to {to_seq} is not allowed",
        )

    if hasattr(current_user, "role") and current_user.role is not None:
        if current_user.role.role_level < transition.min_role:
            raise APIError(
                403,
                "INSUFFICIENT_ROLE_FOR_TRANSITION",
                "Caller's role_level below min_role required for transition",
            )

    doc.doc_state = to_seq
    await db.commit()
    await db.refresh(doc)
    return doc
