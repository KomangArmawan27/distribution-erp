import uuid
from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details=None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def request_id(request: Request | None = None) -> str:
    if request is not None:
        return getattr(request.state, "request_id", "req_unknown")
    return f"req_{uuid.uuid4().hex[:12]}"


def meta(request: Request) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "request_id": request_id(request),
    }


def success(data, message: str, request: Request, pagination: dict | None = None, links: dict | None = None) -> dict:
    body = {"success": True, "message": message, "data": data, "meta": meta(request)}
    if pagination is not None:
        body["pagination"] = pagination
    if links is not None:
        body["links"] = links
    return body


def error(request: Request, status_code: int, code: str, message: str, details=None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "error": {"code": code, "details": details},
            "data": None,
            "meta": meta(request),
        },
    )
