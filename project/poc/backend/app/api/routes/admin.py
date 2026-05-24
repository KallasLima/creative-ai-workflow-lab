from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.security import require_admin
from ...schemas import BrandCreateRequest, TenantCreateRequest
from ...services.admin import create_brand, create_tenant, list_tenants

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])


@router.get("/tenants")
def admin_list_tenants() -> dict:
    return list_tenants()


@router.post("/tenants")
def admin_create_tenant(payload: TenantCreateRequest) -> dict:
    return create_tenant(payload)


@router.post("/tenants/{tenant_id}/brands")
def admin_create_brand(tenant_id: str, payload: BrandCreateRequest) -> dict:
    return create_brand(tenant_id, payload)

