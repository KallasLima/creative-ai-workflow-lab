from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException

from ..core.config import LOCALES, MODEL, NOW
from ..db import connect, insert_audit
from ..providers.mock_model_gateway import copy_variants_for_layer, localized_text_by_locale
from ..schemas import ApplyEventRequest, CopyGenerateRequest, LocalizationRequest
from .brand_profiles import require_scope


def record_operation(
    operation_id: str,
    request_id: str,
    client_request_id: str,
    idempotency_key: str | None,
    tenant_id: str,
    brand_id: str,
    profile_id: str,
    operation_type: str,
    payload: dict[str, Any],
    usage_event_id: str,
    cost: float,
    latency_ms: int,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO operation_requests
            (operation_id, request_id, client_request_id, idempotency_key, tenant_id, brand_id, profile_id, user_id, operation_type, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (operation_id, request_id, client_request_id, idempotency_key, tenant_id, brand_id, profile_id, "usr_maya", operation_type, json.dumps(payload), NOW),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO model_invocations
            (invocation_id, operation_id, provider, model, latency_ms, input_units, output_units, estimated_cost_usd, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (f"invoke_{operation_type}_001", operation_id, "mock-provider", MODEL, latency_ms, 100, 60, cost, NOW),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO usage_events
            (usage_event_id, operation_id, user_id, tenant_id, brand_id, operation_type, estimated_cost_usd, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (usage_event_id, operation_id, "usr_maya", tenant_id, brand_id, operation_type, cost, NOW),
        )
        insert_audit(conn, f"audit_{operation_type}_001", f"{operation_type}_generated", operation_id, usage_event_id, {"clientRequestId": client_request_id})
        conn.commit()


def generate_copy(request: CopyGenerateRequest, idempotency_key: str | None) -> dict[str, Any]:
    require_scope(request.tenantId, request.brandId, request.profileId)
    if request.variantCount > 3:
        raise HTTPException(status_code=400, detail={"code": "invalid_copy_request", "message": "variantCount must be 1-3 for the demo."})
    results = []
    for layer in request.layers:
        variants = copy_variants_for_layer(layer.layerId)
        results.append({"layerId": layer.layerId, "variants": variants[: request.variantCount]})

    record_operation(
        "op_copy_001",
        "req_copy_001",
        request.clientRequestId,
        idempotency_key,
        request.tenantId,
        request.brandId,
        request.profileId,
        "copy",
        request.model_dump(),
        "usage_copy_001",
        0.012,
        420,
    )
    return {
        "requestId": "req_copy_001",
        "operationId": "op_copy_001",
        "status": "completed",
        "profileVersion": request.profileId,
        "brandProfileVersionId": request.profileId,
        "promptTemplateVersionId": "ptv_copy_04",
        "model": MODEL,
        "latencyMs": 420,
        "results": results,
        "usageEventId": "usage_copy_001",
        "usage": {
            "usageEventId": "usage_copy_001",
            "estimatedCostUsd": "0.012",
            "latencyMs": 420,
            "modelProvider": "mock-provider",
            "modelName": MODEL,
        },
    }


def localize_copy(request: LocalizationRequest, idempotency_key: str | None) -> dict[str, Any]:
    require_scope(request.tenantId, request.brandId, request.profileId)
    if len(request.locales) > 8:
        raise HTTPException(status_code=400, detail={"code": "invalid_locale_count", "message": "Localize requests support at most 8 locales."})
    supported_locale_text = localized_text_by_locale()
    unsupported = [locale for locale in request.locales if locale not in supported_locale_text]
    if unsupported:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "unsupported_locale",
                "message": "One or more requested locales are not supported by the pilot contract.",
                "unsupportedLocales": unsupported,
                "supportedLocales": LOCALES,
            },
        )
    requested = request.locales or LOCALES
    results = [
        {
            "layerId": layer.layerId,
            "sourceText": layer.text,
            "localizations": [
                {
                    "locale": locale,
                    "text": localized_text_by_locale(layer.text)[locale],
                    "warning": None if locale != "ja-JP" else "Review character width for compact CTA buttons.",
                }
                for locale in LOCALES
                if locale in requested
            ],
        }
        for layer in request.layers
    ]
    record_operation(
        "op_loc_001",
        "req_loc_001",
        request.clientRequestId,
        idempotency_key,
        request.tenantId,
        request.brandId,
        request.profileId,
        "localization",
        request.model_dump(),
        "usage_loc_001",
        0.009,
        610,
    )
    return {
        "requestId": "req_loc_001",
        "operationId": "op_loc_001",
        "status": "completed",
        "brandProfileVersionId": request.profileId,
        "promptTemplateVersionId": "ptv_localize_04",
        "results": results,
        "usageEventId": "usage_loc_001",
        "usage": {
            "usageEventId": "usage_loc_001",
            "estimatedCostUsd": "0.009",
            "latencyMs": 610,
        },
    }


def record_apply_event(request: ApplyEventRequest) -> dict[str, Any]:
    if not request.appliedItems:
        raise HTTPException(status_code=400, detail={"code": "invalid_apply_event", "message": "At least one applied item is required."})
    with connect() as conn:
        next_index = int(conn.execute("SELECT COUNT(*) AS c FROM apply_events").fetchone()["c"]) + 1
        apply_event_id = f"apply_{next_index:03d}"
        audit_event_id = f"audit_apply_{next_index:03d}"
        request_id = f"req_apply_{next_index:03d}"
        conn.execute(
            """
            INSERT INTO apply_events
            (apply_event_id, operation_id, applied_by, applied_items_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (apply_event_id, request.operationId, request.appliedBy, json.dumps([item.model_dump() for item in request.appliedItems]), NOW),
        )
        insert_audit(conn, audit_event_id, "apply_recorded", request.operationId, payload={"appliedBy": request.appliedBy})
        conn.commit()
    return {"requestId": request_id, "applyEventId": apply_event_id, "auditEventId": audit_event_id, "status": "recorded"}
