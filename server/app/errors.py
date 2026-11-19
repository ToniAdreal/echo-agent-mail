"""Standard success/error envelopes (spec Section 7.3)."""
from __future__ import annotations

import uuid

from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}


def request_id(request: Request) -> str:
    rid = getattr(request.state, "request_id", None)
    if not rid:
        rid = str(uuid.uuid4())
        request.state.request_id = rid
    return rid


def ok(request: Request, data, status: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"data": data, "meta": {"request_id": request_id(request)}},
    )


def error_body(request: Request, err: ApiError) -> dict:
    return {
        "error": {
            "code": err.code,
            "message": err.message,
            "details": err.details,
            "request_id": request_id(request),
        }
    }


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content=error_body(request, exc))
