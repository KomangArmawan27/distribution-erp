from datetime import datetime, timezone

from fastapi import Request


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details=None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "req_unknown")


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


def error(request: Request, code: str, message: str, details=None) -> dict:
    return {
        "success": False,
        "message": message,
        "error": {"code": code, "details": details},
        "data": None,
        "meta": meta(request),
    }