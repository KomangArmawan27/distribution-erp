import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routers import group, item, item_pricelist
from app.routers.group import router as group_router
from app.routers.item import router as item_router
from app.routers.item_pricelist import router as price_router
from app.utils.response import APIError

load_dotenv()

app = FastAPI(title="ERP Backend — Item Master", version="0.1.0")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = f"req_{uuid.uuid4().hex[:12]}"
    response = await call_next(request)
    return response


def _meta(request: Request) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "request_id": getattr(request.state, "request_id", "req_unknown"),
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [
        {"field": ".".join(str(p) for p in e["loc"] if p not in ("body", "query", "path")), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation failed",
            "error": {"code": "VALIDATION_ERROR", "details": details},
            "data": None,
            "meta": _meta(request),
        },
    )


@app.exception_handler(APIError)
async def api_error_exception_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error": {"code": exc.code, "details": exc.details},
            "data": None,
            "meta": _meta(request),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": {"code": "INTERNAL_ERROR", "details": None},
            "data": None,
            "meta": _meta(request),
        },
    )


app.include_router(item_router)
app.include_router(group_router)
app.include_router(price_router)


@app.get("/health")
async def health(request: Request):
    return {"status": "ok", "meta": _meta(request)}