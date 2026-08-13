from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.item import item_crud
from app.config.database import get_db
from app.utils.pagination import build_links, pagination_dict
from app.utils.response import APIError, success
from app.schemas.envelope import Envelope
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["Item Master"])


@router.get("/", response_model=Envelope[list[ItemRead]], response_model_exclude_none=True)
async def list_items(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    page_result = await item_crud.page(db, page=page, per_page=per_page)
    data = [ItemRead.model_validate(obj) for obj in page_result.items]
    return success(
        data,
        "Items fetched successfully",
        request,
        pagination=pagination_dict(page_result),
        links=build_links(request, page, per_page, page_result),
    )


@router.get("/{item_id}", response_model=Envelope[ItemRead], response_model_exclude_none=True)
async def get_item(item_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await item_crud.get(db, item_id)
    if not obj:
        raise APIError(404, "ITEM_NOT_FOUND", "Item not found")
    return success(ItemRead.model_validate(obj), "Item fetched successfully", request)


@router.post("/", response_model=Envelope[ItemRead], response_model_exclude_none=True, status_code=201)
async def create_item(payload: ItemCreate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        obj = await item_crud.create(db, payload)
    except ValueError as e:
        raise APIError(422, "VALIDATION_ERROR", "Validation failed", [{"field": "group", "message": str(e)}])
    return success(ItemRead.model_validate(obj), "Item created successfully", request)


@router.put("/{item_id}", response_model=Envelope[ItemRead], response_model_exclude_none=True)
async def update_item(item_id: int, payload: ItemUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await item_crud.get(db, item_id)
    if not obj:
        raise APIError(404, "ITEM_NOT_FOUND", "Item not found")
    try:
        obj = await item_crud.update(db, obj, payload)
    except ValueError as e:
        raise APIError(422, "VALIDATION_ERROR", "Validation failed", [{"field": "group", "message": str(e)}])
    return success(ItemRead.model_validate(obj), "Item updated successfully", request)


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    ok = await item_crud.delete(db, item_id)
    if not ok:
        raise APIError(404, "ITEM_NOT_FOUND", "Item not found")