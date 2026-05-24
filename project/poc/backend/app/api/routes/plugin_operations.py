from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import Response

from ...core.security import require_auth, require_versions
from ...schemas import ApplyEventRequest, CopyGenerateRequest, ImageJobRequest, LocalizationRequest
from ...services.image_jobs import create_image_job, get_asset_png, get_image_job
from ...services.model_operations import generate_copy, localize_copy, record_apply_event

router = APIRouter()
protected_router = APIRouter(dependencies=[Depends(require_auth)])


@protected_router.post("/plugin/copy/generate")
def copy_generate(request: CopyGenerateRequest, idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None) -> dict:
    require_versions(request.contractVersion, request.pluginVersion)
    return generate_copy(request, idempotency_key)


@protected_router.post("/plugin/copy/localize")
def copy_localize(request: LocalizationRequest, idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None) -> dict:
    require_versions(request.contractVersion, request.pluginVersion)
    return localize_copy(request, idempotency_key)


@protected_router.post("/plugin/images/jobs")
def image_job_create(request: ImageJobRequest, idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None) -> dict:
    require_versions(request.contractVersion, request.pluginVersion)
    return create_image_job(request, idempotency_key)


@protected_router.get("/plugin/images/jobs/{job_id}")
def image_job_status(job_id: str, request: Request) -> dict:
    return get_image_job(job_id, request)


@router.get("/assets/{asset_id}.png")
def asset_png(asset_id: str) -> Response:
    return Response(content=get_asset_png(asset_id), media_type="image/png")


@protected_router.post("/plugin/apply-events")
def apply_event(request: ApplyEventRequest) -> dict:
    return record_apply_event(request)

