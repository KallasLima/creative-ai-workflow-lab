from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import HTTPException


def error_response(
    request_id: str,
    code: str,
    message: str,
    status_code: int,
    *,
    retryable: bool = False,
    user_action: str | None = None,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    category_by_code = {
        "unauthorized": "auth",
        "unauthorized_brand": "policy",
        "profile_not_found": "validation",
        "contract_mismatch": "validation",
        "unsupported_file_type": "validation",
        "file_too_large": "validation",
        "invalid_locale_count": "validation",
        "unsupported_locale": "validation",
        "invalid_layer_dimensions": "validation",
        "invalid_image_layer": "validation",
        "invalid_copy_request": "validation",
        "invalid_apply_event": "validation",
        "invalid_profile_approval": "validation",
        "job_not_found": "job",
        "asset_not_found": "asset",
        "brand_not_found": "policy",
        "profile_inactive": "policy",
        "image_prompt_requires_review": "policy",
        "auth_request_invalid": "auth",
        "guideline_not_found": "validation",
        "apply_not_found": "validation",
        "admin_required": "auth",
        "quality_gate_failed": "quality",
    }
    return JSONResponse(
        status_code=status_code,
        content={
            "requestId": request_id,
            "error": {
                "code": code,
                "category": category_by_code.get(code, "unknown"),
                "message": message,
                "retryable": retryable,
                "userAction": user_action,
                "details": details or {},
            },
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
    request_id = request.headers.get("x-request-id", "req_error")
    return error_response(
        request_id,
        detail.get("code", f"http_{exc.status_code}"),
        detail.get("message", "Request failed."),
        exc.status_code,
        retryable=bool(detail.get("retryable", False)),
        user_action=detail.get("userAction"),
        details={k: v for k, v in detail.items() if k not in {"code", "message", "retryable", "userAction"}},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        request.headers.get("x-request-id", "req_error"),
        "validation_error",
        "Request validation failed.",
        422,
        details={"errors": exc.errors()},
    )

