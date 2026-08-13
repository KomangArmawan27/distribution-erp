from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class MetaModel(BaseModel):
    timestamp: str
    request_id: str


class ErrorModel(BaseModel):
    code: str
    details: Any = None


class PaginationModel(BaseModel):
    page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class LinksModel(BaseModel):
    self: str
    next: str | None
    prev: str | None


class Envelope(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None
    pagination: PaginationModel | None = None
    links: LinksModel | None = None
    error: ErrorModel | None = None
    meta: MetaModel