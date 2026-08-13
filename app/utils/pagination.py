import math
from dataclasses import dataclass

from fastapi import Request


@dataclass
class PageResult:
    items: list
    page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


def build_links(request: Request, page: int, per_page: int, page_result: PageResult) -> dict:
    base = str(request.url).split("?", 1)[0]

    def make_url(p: int) -> str:
        return f"{base}?page={p}&per_page={per_page}"

    return {
        "self": make_url(page),
        "next": make_url(page + 1) if page_result.has_next else None,
        "prev": make_url(page - 1) if page_result.has_prev else None,
    }


def pagination_dict(page_result: PageResult) -> dict:
    return {
        "page": page_result.page,
        "per_page": page_result.per_page,
        "total_items": page_result.total_items,
        "total_pages": page_result.total_pages,
        "has_next": page_result.has_next,
        "has_prev": page_result.has_prev,
    }


def compute_page_result(
    items: list, page: int, per_page: int, total_items: int, total_pages: int | None = None
) -> PageResult:
    if total_pages is None:
        total_pages = math.ceil(total_items / per_page) if per_page else 0
    return PageResult(
        items=items,
        page=page,
        per_page=per_page,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )