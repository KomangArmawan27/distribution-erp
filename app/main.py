from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from app.modules.group.router import router as group_router
from app.modules.system.router import router as system_router
from app.modules.item.router import router as item_router
from app.modules.item_pricelist.router import router as price_router
from app.modules.employee.router import router as employee_router
from app.modules.sales_person.router import router as sales_person_router
from app.modules.customer.router import router as customer_router
from app.modules.sales_order.router import router as sales_order_router
from app.core.response import APIError, error, meta, request_id

load_dotenv()

app = FastAPI(title="ERP Backend — Sales Order Module & Flow State", version="0.1.0")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = request_id()
    response = await call_next(request)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
    return error(request, status_code=422, code="VALIDATION_ERROR", message="Validation failed", details=details)


@app.exception_handler(APIError)
async def api_error_exception_handler(request: Request, exc: APIError):
    return error(request, status_code=exc.status_code, code=exc.code, message=exc.message, details=exc.details)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return error(request, status_code=500, code="INTERNAL_ERROR", message="An unexpected error occurred")


@app.get("/health")
async def health(request: Request):
    return {"status": "ok", "meta": meta(request)}


app.include_router(group_router)
app.include_router(system_router)
app.include_router(item_router)
app.include_router(price_router)
app.include_router(employee_router)
app.include_router(sales_person_router)
app.include_router(customer_router)
app.include_router(sales_order_router)
