from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.group import group_crud
from app.config.database import get_db
from app.models import Group
from app.utils.pagination import build_links, pagination_dict
from app.utils.response import APIError, success
from app.schemas.envelope import Envelope
from app.schemas.group import GroupCreate, GroupRead, GroupUpdate

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("/", response_model=Envelope[list[GroupRead]], response_model_exclude_none=True)
async def list_groups(
    request: Request,
    group_name: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    extra_filter = Group.group_name == group_name if group_name else None
    page_result = await group_crud.page(db, page=page, per_page=per_page, extra_filter=extra_filter)
    data = [GroupRead.model_validate(obj) for obj in page_result.items]
    return success(
        data,
        "Groups fetched successfully",
        request,
        pagination=pagination_dict(page_result),
        links=build_links(request, page, per_page, page_result),
    )


@router.get("/{group_id}", response_model=Envelope[GroupRead], response_model_exclude_none=True)
async def get_group(group_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await group_crud.get(db, group_id)
    if not obj:
        raise APIError(404, "GROUP_NOT_FOUND", "Group not found")
    return success(GroupRead.model_validate(obj), "Group fetched successfully", request)


@router.post("/", response_model=Envelope[GroupRead], status_code=201, response_model_exclude_none=True)
async def create_group(payload: GroupCreate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await group_crud.create(db, payload)
    return success(GroupRead.model_validate(obj), "Group created successfully", request)


@router.put("/{group_id}", response_model=Envelope[GroupRead], response_model_exclude_none=True)
async def update_group(group_id: int, payload: GroupUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await group_crud.get(db, group_id)
    if not obj:
        raise APIError(404, "GROUP_NOT_FOUND", "Group not found")
    obj = await group_crud.update(db, obj, payload)
    return success(GroupRead.model_validate(obj), "Group updated successfully", request)


@router.delete("/{group_id}", status_code=204)
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    ok = await group_crud.delete(db, group_id)
    if not ok:
        raise APIError(404, "GROUP_NOT_FOUND", "Group not found")