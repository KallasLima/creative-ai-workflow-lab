from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.security import require_auth

router = APIRouter(dependencies=[Depends(require_auth)])


@router.get("/me/context")
def context() -> dict:
    return {
        "requestId": "req_context_001",
        "tenant": {"tenantId": "tenant_designtechco", "name": "DesignTechCo"},
        "user": {"userId": "usr_maya", "displayName": "Maya Chen", "role": "designer"},
        "brands": [{"brandId": "brand_nova", "name": "Nova Athletics", "activeProfileId": "profile_nova_v3"}],
        "tenants": [
            {
                "tenantId": "tenant_designtechco",
                "name": "DesignTechCo",
                "brands": [
                    {
                        "brandId": "brand_nova",
                        "name": "Nova Athletics",
                        "activeProfileVersionId": "profile_nova_v3",
                        "enabledOperations": ["copy_variants", "localize", "image_placeholder"],
                    }
                ],
            }
        ],
        "featureFlags": {"imagePlaceholders": True, "pdfIngestion": True, "usageReporting": True},
        "limits": {"maxTextLayersPerRequest": 20, "maxLocalesPerRequest": 8, "maxImageJobsPerUser": 3},
    }

