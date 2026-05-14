"""Shared error helpers — standard JSON error envelope."""
from fastapi import HTTPException


def not_found(resource: str = "Resource") -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": f"{resource} not found"})


def bad_request(message: str, code: str = "BAD_REQUEST") -> HTTPException:
    return HTTPException(status_code=400, detail={"code": code, "message": message})


def conflict(message: str, code: str = "CONFLICT") -> HTTPException:
    return HTTPException(status_code=409, detail={"code": code, "message": message})


def unauthorized(message: str = "Unauthorized") -> HTTPException:
    return HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": message})


def forbidden(message: str = "Forbidden") -> HTTPException:
    return HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": message})


def ok(data, meta: dict | None = None) -> dict:
    """Standard success envelope."""
    result = {"data": data}
    if meta:
        result["meta"] = meta
    return result
