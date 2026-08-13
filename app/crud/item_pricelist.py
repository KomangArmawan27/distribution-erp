from app.crud.base import CRUDBase
from app.models import ItemPriceList
from app.schemas.item_pricelist import ItemPriceListCreate, ItemPriceListUpdate

item_pricelist_crud = CRUDBase[ItemPriceList, ItemPriceListCreate, ItemPriceListUpdate](ItemPriceList)