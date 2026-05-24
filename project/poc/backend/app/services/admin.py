from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from ..db import connect, insert_audit
from ..schemas import BrandCreateRequest, TenantCreateRequest


def list_tenants() -> dict[str, Any]:
    with connect() as conn:
        tenants = conn.execute("SELECT tenant_id, name FROM tenants ORDER BY tenant_id").fetchall()
        brands = conn.execute("SELECT tenant_id, brand_id, name, active_profile_id FROM brands ORDER BY tenant_id, brand_id").fetchall()
        users = conn.execute("SELECT tenant_id, user_id, display_name, role FROM users ORDER BY tenant_id, user_id").fetchall()
    brands_by_tenant: dict[str, list[dict[str, Any]]] = {}
    for brand in brands:
        brands_by_tenant.setdefault(brand["tenant_id"], []).append(
            {"brandId": brand["brand_id"], "name": brand["name"], "activeProfileId": brand["active_profile_id"] or None}
        )
    users_by_tenant: dict[str, list[dict[str, Any]]] = {}
    for user in users:
        users_by_tenant.setdefault(user["tenant_id"], []).append(
            {"userId": user["user_id"], "displayName": user["display_name"], "role": user["role"]}
        )
    return {
        "requestId": "req_admin_tenants_001",
        "tenants": [
            {"tenantId": tenant["tenant_id"], "name": tenant["name"], "brands": brands_by_tenant.get(tenant["tenant_id"], []), "users": users_by_tenant.get(tenant["tenant_id"], [])}
            for tenant in tenants
        ],
    }


def create_tenant(payload: TenantCreateRequest) -> dict[str, Any]:
    with connect() as conn:
        conn.execute("INSERT OR IGNORE INTO tenants (tenant_id, name) VALUES (?, ?)", (payload.tenantId, payload.name))
        insert_audit(conn, "audit_admin_tenant_001", "tenant_created", payload={"tenantId": payload.tenantId})
        conn.commit()
    return {"requestId": "req_admin_tenant_create_001", "tenantId": payload.tenantId, "status": "ready"}


def create_brand(tenant_id: str, payload: BrandCreateRequest) -> dict[str, Any]:
    with connect() as conn:
        tenant = conn.execute("SELECT tenant_id FROM tenants WHERE tenant_id = ?", (tenant_id,)).fetchone()
        if not tenant:
            raise HTTPException(status_code=404, detail={"code": "tenant_not_found", "message": "Tenant was not found."})
        conn.execute(
            "INSERT OR IGNORE INTO brands (brand_id, tenant_id, name, active_profile_id) VALUES (?, ?, ?, ?)",
            (payload.brandId, tenant_id, payload.name, ""),
        )
        insert_audit(conn, "audit_admin_brand_001", "brand_created", payload={"tenantId": tenant_id, "brandId": payload.brandId})
        conn.commit()
    return {"requestId": "req_admin_brand_create_001", "tenantId": tenant_id, "brandId": payload.brandId, "status": "ready"}

