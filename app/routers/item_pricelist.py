from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.item_pricelist import item_pricelist_crud
from app.config.database import get_db
from app.utils.pagination import build_links, pagination_dict
from app.utils.response import APIError, success
from app.schemas.envelope import Envelope
from app.schemas.item_pricelist import ItemPriceListCreate, ItemPriceListRead, ItemPriceListUpdate

router = APIRouter(prefix="/item-pricelist", tags=["Item Price List"])


@router.get("/", response_model=Envelope[list[ItemPriceListRead]], response_model_exclude_none=True)
async def list_prices(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    page_result = await item_pricelist_crud.page(db, page=page, per_page=per_page)
    data = [ItemPriceListRead.model_validate(obj) for obj in page_result.items]
    return success(
        data,
        "Price records fetched successfully",
        request,
        pagination=pagination_dict(page_result),
        links=build_links(request, page, per_page, page_result),
    )


@router.get("/{price_id}", response_model=Envelope[ItemPriceListRead], response_model_exclude_none=True)
async def get_price(price_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await item_pricelist_crud.get(db, price_id)
    if not obj:
        raise APIError(404, "PRICE_NOT_FOUND", "Price record not found")
    return success(ItemPriceListRead.model_validate(obj), "Price record fetched successfully", request)


@router.post("/", response_model=Envelope[ItemPriceListRead], response_model_exclude_none=True, status_code=201)
async def create_price(payload: ItemPriceListCreate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await item_pricelist_crud.create(db, payload)
    return success(ItemPriceListRead.model_validate(obj), "Price record created successfully", request)


@router.put("/{price_id}", response_model=Envelope[ItemPriceListRead], response_model_exclude_none=True)
async def update_price(price_id: int, payload: ItemPriceListUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    obj = await item_pricelist_crud.get(db, price_id)
    if not obj:
        raise APIError(404, "PRICE_NOT_FOUND", "Price record not found")
    obj = await item_pricelist_crud.update(db, obj, payload)
    return success(ItemPriceListRead.model_validate(obj), "Price record updated successfully", request)


@router.delete("/{price_id}", status_code=204)
async def delete_price(price_id: int, db: AsyncSession = Depends(get_db)):
    ok = await item_pricelist_crud.delete(db, price_id)
    if not ok:
        raise APIError(404, "PRICE_NOT_FOUND", "Price record not found")