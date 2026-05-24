from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ...core.security import require_auth
from ...schemas import ApproveProfileRequest
from ...services.brand_profiles import approve_brand_profile, get_brand_profile, list_brand_profiles, upload_guideline_and_approve_profile

router = APIRouter(dependencies=[Depends(require_auth)])


@router.post("/tenants/{tenant_id}/brands/{brand_id}/guidelines")
async def upload_guideline(tenant_id: str, brand_id: str, file: UploadFile = File(...)) -> dict:
    return await upload_guideline_and_approve_profile(tenant_id, brand_id, file)


@router.get("/tenants/{tenant_id}/brands/{brand_id}/profiles")
def list_profiles(tenant_id: str, brand_id: str) -> dict:
    return list_brand_profiles(tenant_id, brand_id)


@router.get("/tenants/{tenant_id}/brands/{brand_id}/profiles/{profile_id}")
def get_profile(tenant_id: str, brand_id: str, profile_id: str) -> dict:
    return get_brand_profile(tenant_id, brand_id, profile_id)


@router.post("/tenants/{tenant_id}/brands/{brand_id}/profiles/{profile_id}/approve")
def approve_profile(tenant_id: str, brand_id: str, profile_id: str, payload: ApproveProfileRequest) -> dict:
    if not payload.approved or not payload.makeActive:
        raise HTTPException(status_code=400, detail={"code": "invalid_profile_approval", "message": "Approval must mark the profile active."})
    return approve_brand_profile(tenant_id, brand_id, profile_id, payload.reviewComment)

