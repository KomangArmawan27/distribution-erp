from typing import Generic, Sequence, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import Base
from app.utils.pagination import compute_page_result, PageResult

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
        self.pk_column = list(self.model.__mapper__.primary_key)[0]

    async def get(self, db: AsyncSession, id_: int) -> ModelType | None:
        return await db.get(self.model, id_)

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def page(
        self,
        db: AsyncSession,
        page: int = 1,
        per_page: int = 20,
        extra_filter=None,
    ) -> PageResult:
        pk = self.pk_column
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)
        if extra_filter is not None:
            stmt = stmt.where(extra_filter)
            count_stmt = count_stmt.where(extra_filter)

        total_items = (await db.execute(count_stmt)).scalar() or 0
        total_pages = max((total_items + per_page - 1) // per_page, 0) if per_page else 0

        if page > total_pages and total_pages > 0:
            page = total_pages
        if page < 1:
            page = 1

        offset = (page - 1) * per_page
        rows = (await db.execute(stmt.order_by(pk.desc()).offset(offset).limit(per_page))).unique().scalars().all()

        return compute_page_result(list(rows), page, per_page, total_items, total_pages)

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id_: int) -> bool:
        db_obj = await self.get(db, id_)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.commit()
        return True