from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import build_links, pagination_dict
from app.core.response import APIError, success
from app.core.envelope import Envelope
from app.modules.system.crud import (
    document_type_crud,
    flow_state_crud,
    flow_transition_crud,
)
from app.modules.system.models import DocumentType, FlowState, FlowTransition
from app.modules.system.schemas import (
    DocumentTypeCreate,
    DocumentTypeRead,
    DocumentTypeUpdate,
    FlowStateCreate,
    FlowStateRead,
    FlowStateUpdate,
    FlowTransitionCreate,
    FlowTransitionRead,
    FlowTransitionUpdate,
)
from app.modules.sales_order.models import OrderHeader

router = APIRouter(tags=["System / Flow Management"])


# --- Document Types ---

@router.get("/document-types/", response_model=Envelope[list[DocumentTypeRead]], response_model_exclude_none=True)
async def list_document_types(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    page_result = await document_type_crud.page(db, page=page, per_page=per_page)
    data = [DocumentTypeRead.model_validate(obj) for obj in page_result.items]
    return success(
        data,
        "Document types fetched successfully",
        request,
        pagination=pagination_dict(page_result),
        links=build_links(request, page, per_page, page_result),
    )


@router.get("/document-types/{doctype_id}", response_model=Envelope[DocumentTypeRead], response_model_exclude_none=True)
async def get_document_type(doctype_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await document_type_crud.get(db, doctype_id)
    if not obj:
        raise APIError(404, "DOCUMENT_TYPE_NOT_FOUND", f"Document type {doctype_id} not found")
    return success(DocumentTypeRead.model_validate(obj), "Document type fetched successfully", request)


@router.post("/document-types/", response_model=Envelope[DocumentTypeRead], status_code=201, response_model_exclude_none=True)
async def create_document_type(payload: DocumentTypeCreate, request: Request, db: AsyncSession = Depends(get_db)):
    # Check unique code conflict
    existing = (await db.execute(select(DocumentType).where(DocumentType.doctype_code == payload.doctype_code))).scalar_one_or_none()
    if existing:
        raise APIError(409, "DOCUMENT_TYPE_CODE_CONFLICT", f"Document type code '{payload.doctype_code}' already exists")
    obj = await document_type_crud.create(db, payload)
    return success(DocumentTypeRead.model_validate(obj), "Document type created successfully", request)


@router.put("/document-types/{doctype_id}", response_model=Envelope[DocumentTypeRead], response_model_exclude_none=True)
async def update_document_type(doctype_id: int, payload: DocumentTypeUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await document_type_crud.get(db, doctype_id)
    if not obj:
        raise APIError(404, "DOCUMENT_TYPE_NOT_FOUND", f"Document type {doctype_id} not found")
    if payload.doctype_code is not None and payload.doctype_code != obj.doctype_code:
        existing = (await db.execute(select(DocumentType).where(DocumentType.doctype_code == payload.doctype_code))).scalar_one_or_none()
        if existing:
            raise APIError(409, "DOCUMENT_TYPE_CODE_CONFLICT", f"Document type code '{payload.doctype_code}' already exists")
    obj = await document_type_crud.update(db, obj, payload)
    return success(DocumentTypeRead.model_validate(obj), "Document type updated successfully", request)


@router.delete("/document-types/{doctype_id}", status_code=204)
async def delete_document_type(doctype_id: int, db: AsyncSession = Depends(get_db)):
    obj = await document_type_crud.get(db, doctype_id)
    if not obj:
        raise APIError(404, "DOCUMENT_TYPE_NOT_FOUND", f"Document type {doctype_id} not found")
    
    # Check if any flow_state references it
    fs_count = (await db.execute(select(FlowState).where(FlowState.doctype_id == doctype_id))).first()
    if fs_count:
        raise APIError(409, "DOCUMENT_TYPE_IN_USE", "Cannot delete document type because flow states reference it")
    
    await document_type_crud.delete(db, doctype_id)


# --- Flow States ---

@router.get("/flow-states/", response_model=Envelope[list[FlowStateRead]], response_model_exclude_none=True)
async def list_flow_states(
    request: Request,
    doctype_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    extra_filter = FlowState.doctype_id == doctype_id if doctype_id is not None else None
    page_result = await flow_state_crud.page(db, page=page, per_page=per_page, extra_filter=extra_filter)
    data = [FlowStateRead.model_validate(obj) for obj in page_result.items]
    return success(
        data,
        "Flow states fetched successfully",
        request,
        pagination=pagination_dict(page_result),
        links=build_links(request, page, per_page, page_result),
    )


@router.get("/flow-states/{flow_id}", response_model=Envelope[FlowStateRead], response_model_exclude_none=True)
async def get_flow_state(flow_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await flow_state_crud.get(db, flow_id)
    if not obj:
        raise APIError(404, "FLOW_STATE_NOT_FOUND", f"Flow state {flow_id} not found")
    return success(FlowStateRead.model_validate(obj), "Flow state fetched successfully", request)


@router.post("/flow-states/", response_model=Envelope[FlowStateRead], status_code=201, response_model_exclude_none=True)
async def create_flow_state(payload: FlowStateCreate, request: Request, db: AsyncSession = Depends(get_db)):
    # 1. doctype_id must exist
    dt = await document_type_crud.get(db, payload.doctype_id)
    if not dt:
        raise APIError(404, "DOCUMENT_TYPE_NOT_FOUND", f"Document type {payload.doctype_id} not found")
    
    # 2. (doctype_id, docflow_seq) must not exist
    seq_conflict = (await db.execute(
        select(FlowState).where(FlowState.doctype_id == payload.doctype_id, FlowState.docflow_seq == payload.docflow_seq)
    )).scalar_one_or_none()
    if seq_conflict:
        raise APIError(409, "FLOW_STATE_SEQ_CONFLICT", f"Flow state sequence {payload.docflow_seq} already exists for doctype {payload.doctype_id}")

    # 3. (doctype_id, flow_state) must not exist
    label_conflict = (await db.execute(
        select(FlowState).where(FlowState.doctype_id == payload.doctype_id, FlowState.flow_state == payload.flow_state)
    )).scalar_one_or_none()
    if label_conflict:
        raise APIError(409, "FLOW_STATE_LABEL_CONFLICT", f"Flow state label '{payload.flow_state}' already exists for doctype {payload.doctype_id}")

    obj = await flow_state_crud.create(db, payload)
    return success(FlowStateRead.model_validate(obj), "Flow state created successfully", request)


@router.put("/flow-states/{flow_id}", response_model=Envelope[FlowStateRead], response_model_exclude_none=True)
async def update_flow_state(flow_id: int, payload: FlowStateUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await flow_state_crud.get(db, flow_id)
    if not obj:
        raise APIError(404, "FLOW_STATE_NOT_FOUND", f"Flow state {flow_id} not found")
    
    changes = payload.model_dump(exclude_unset=True)
    new_seq = changes.get("docflow_seq", obj.docflow_seq)
    new_label = changes.get("flow_state", obj.flow_state)

    if new_seq != obj.docflow_seq:
        seq_conflict = (await db.execute(
            select(FlowState).where(FlowState.doctype_id == obj.doctype_id, FlowState.docflow_seq == new_seq, FlowState.flow_id != flow_id)
        )).scalar_one_or_none()
        if seq_conflict:
            raise APIError(409, "FLOW_STATE_SEQ_CONFLICT", f"Flow state sequence {new_seq} already exists for doctype {obj.doctype_id}")

    if new_label != obj.flow_state:
        label_conflict = (await db.execute(
            select(FlowState).where(FlowState.doctype_id == obj.doctype_id, FlowState.flow_state == new_label, FlowState.flow_id != flow_id)
        )).scalar_one_or_none()
        if label_conflict:
            raise APIError(409, "FLOW_STATE_LABEL_CONFLICT", f"Flow state label '{new_label}' already exists for doctype {obj.doctype_id}")

    obj = await flow_state_crud.update(db, obj, payload)
    return success(FlowStateRead.model_validate(obj), "Flow state updated successfully", request)


@router.delete("/flow-states/{flow_id}", status_code=204)
async def delete_flow_state(flow_id: int, db: AsyncSession = Depends(get_db)):
    obj = await flow_state_crud.get(db, flow_id)
    if not obj:
        raise APIError(404, "FLOW_STATE_NOT_FOUND", f"Flow state {flow_id} not found")
    
    # 1. Check if any transition references this state (from_seq or to_seq)
    trans_ref = (await db.execute(
        select(FlowTransition).where(
            FlowTransition.doctype_id == obj.doctype_id,
            (FlowTransition.from_seq == obj.docflow_seq) | (FlowTransition.to_seq == obj.docflow_seq)
        )
    )).first()
    if trans_ref:
        raise APIError(409, "FLOW_STATE_IN_USE", "Cannot delete flow state because transitions reference it")

    # 2. Check if any live document row sits on this state (e.g. sales.order_header)
    if obj.doctype_id == 1:
        doc_ref = (await db.execute(
            select(OrderHeader).where(OrderHeader.doctype_id == 1, OrderHeader.doc_state == obj.docflow_seq)
        )).first()
        if doc_ref:
            raise APIError(409, "FLOW_STATE_IN_USE", "Cannot delete flow state because live documents reference it")

    await flow_state_crud.delete(db, flow_id)


# --- Flow Transitions ---

@router.get("/flow-transitions/", response_model=Envelope[list[FlowTransitionRead]], response_model_exclude_none=True)
async def list_flow_transitions(
    request: Request,
    doctype_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    extra_filter = FlowTransition.doctype_id == doctype_id if doctype_id is not None else None
    page_result = await flow_transition_crud.page(db, page=page, per_page=per_page, extra_filter=extra_filter)
    data = [FlowTransitionRead.model_validate(obj) for obj in page_result.items]
    return success(
        data,
        "Flow transitions fetched successfully",
        request,
        pagination=pagination_dict(page_result),
        links=build_links(request, page, per_page, page_result),
    )


@router.get("/flow-transitions/{transition_id}", response_model=Envelope[FlowTransitionRead], response_model_exclude_none=True)
async def get_flow_transition(transition_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await flow_transition_crud.get(db, transition_id)
    if not obj:
        raise APIError(404, "FLOW_TRANSITION_NOT_FOUND", f"Flow transition {transition_id} not found")
    return success(FlowTransitionRead.model_validate(obj), "Flow transition fetched successfully", request)


@router.post("/flow-transitions/", response_model=Envelope[FlowTransitionRead], status_code=201, response_model_exclude_none=True)
async def create_flow_transition(payload: FlowTransitionCreate, request: Request, db: AsyncSession = Depends(get_db)):
    # 1. doctype_id must exist
    dt = await document_type_crud.get(db, payload.doctype_id)
    if not dt:
        raise APIError(404, "DOCUMENT_TYPE_NOT_FOUND", f"Document type {payload.doctype_id} not found")

    # 2. from_seq must exist in flow_state
    from_state = (await db.execute(
        select(FlowState).where(FlowState.doctype_id == payload.doctype_id, FlowState.docflow_seq == payload.from_seq)
    )).scalar_one_or_none()
    if not from_state:
        raise APIError(404, "FLOW_STATE_NOT_FOUND", f"Source flow state sequence {payload.from_seq} not found for doctype {payload.doctype_id}")

    # 3. to_seq must exist in flow_state
    to_state = (await db.execute(
        select(FlowState).where(FlowState.doctype_id == payload.doctype_id, FlowState.docflow_seq == payload.to_seq)
    )).scalar_one_or_none()
    if not to_state:
        raise APIError(404, "FLOW_STATE_NOT_FOUND", f"Target flow state sequence {payload.to_seq} not found for doctype {payload.doctype_id}")

    # 4. from_seq != to_seq
    if payload.from_seq == payload.to_seq:
        raise APIError(422, "INVALID_TRANSITION_SAME_STATE", "Transition to the same state is not meaningful")

    obj = await flow_transition_crud.create(db, payload)
    return success(FlowTransitionRead.model_validate(obj), "Flow transition created successfully", request)


@router.put("/flow-transitions/{transition_id}", response_model=Envelope[FlowTransitionRead], response_model_exclude_none=True)
async def update_flow_transition(transition_id: int, payload: FlowTransitionUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await flow_transition_crud.get(db, transition_id)
    if not obj:
        raise APIError(404, "FLOW_TRANSITION_NOT_FOUND", f"Flow transition {transition_id} not found")
    obj = await flow_transition_crud.update(db, obj, payload)
    return success(FlowTransitionRead.model_validate(obj), "Flow transition updated successfully", request)


@router.delete("/flow-transitions/{transition_id}", status_code=204)
async def delete_flow_transition(transition_id: int, db: AsyncSession = Depends(get_db)):
    obj = await flow_transition_crud.get(db, transition_id)
    if not obj:
        raise APIError(404, "FLOW_TRANSITION_NOT_FOUND", f"Flow transition {transition_id} not found")
    await flow_transition_crud.delete(db, transition_id)
