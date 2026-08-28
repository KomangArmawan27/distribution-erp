from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.group.crud import group_crud
from app.core.database import get_db
from app.modules.group.models import Group
from app.core.pagination import build_links, pagination_dict
from app.core.response import APIError, success
from app.core.envelope import Envelope
from app.modules.group.schemas import GroupCreate, GroupRead, GroupUpdate

router = APIRouter(prefix="/groups", tags=["Groups"])


async def _ensure_noid_free(db: AsyncSession, group_name: str, group_noid: int, exclude_group_id: int | None = None) -> None:
    stmt = select(Group.group_id).where(Group.group_name == group_name, Group.group_noid == group_noid)
    if exclude_group_id is not None:
        stmt = stmt.where(Group.group_id != exclude_group_id)
    if (await db.execute(stmt)).scalar_one_or_none() is not None:
        raise APIError(
            409,
            "GROUP_NOID_TAKEN",
            f"group_noid {group_noid} is already taken for group '{group_name}'",
        )


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
        raise APIError(404, "GROUP_NOT_FOUND", f"Group {group_id} not found")
    return success(GroupRead.model_validate(obj), "Group fetched successfully", request)


@router.post("/", response_model=Envelope[GroupRead], status_code=201, response_model_exclude_none=True)
async def create_group(payload: GroupCreate, request: Request, db: AsyncSession = Depends(get_db)):
    await _ensure_noid_free(db, payload.group_name, payload.group_noid)
    obj = await group_crud.create(db, payload)
    return success(GroupRead.model_validate(obj), "Group created successfully", request)


@router.put("/{group_id}", response_model=Envelope[GroupRead], response_model_exclude_none=True)
async def update_group(group_id: int, payload: GroupUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await group_crud.get(db, group_id)
    if not obj:
        raise APIError(404, "GROUP_NOT_FOUND", f"Group {group_id} not found")
    changes = payload.model_dump(exclude_unset=True)
    group_name = changes.get("group_name", obj.group_name)
    group_noid = changes.get("group_noid", obj.group_noid)
    if changes:
        await _ensure_noid_free(db, group_name, group_noid, exclude_group_id=group_id)
    obj = await group_crud.update(db, obj, payload)
    return success(GroupRead.model_validate(obj), "Group updated successfully", request)


@router.delete("/{group_id}", status_code=204)
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    ok = await group_crud.delete(db, group_id)
    if not ok:
        raise APIError(404, "GROUP_NOT_FOUND", f"Group {group_id} not found")
