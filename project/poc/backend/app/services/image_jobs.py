from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import HTTPException, Request

from ..core.config import MODEL, NOW
from ..db import connect, insert_audit
from ..domain.image_policy import IMAGE_POLICY_CHECKS, evaluate_image_prompt_policy
from ..png import generate_placeholder_png
from ..schemas import ImageJobRequest
from .brand_profiles import require_scope


def create_image_job(request: ImageJobRequest, idempotency_key: str | None) -> dict[str, Any]:
    require_scope(request.tenantId, request.brandId, request.profileId)
    if request.layer.type != "imageFill":
        raise HTTPException(status_code=400, detail={"code": "invalid_image_layer", "message": "Image jobs require an imageFill layer."})
    if request.layer.dimensions.width != 1024 or request.layer.dimensions.height != 1024:
        raise HTTPException(status_code=400, detail={"code": "invalid_layer_dimensions", "message": "Image placeholder jobs must target 1024 x 1024 layers."})
    policy = evaluate_image_prompt_policy(request.prompt)
    if not policy["allowed"]:
        prompt_hash = hashlib.sha256(request.prompt.encode()).hexdigest()
        with connect() as conn:
            insert_audit(
                conn,
                "audit_image_policy_blocked_001",
                "image_prompt_requires_review",
                request.clientRequestId,
                payload={
                    "layerId": request.layer.layerId,
                    "promptHash": prompt_hash,
                    "categories": policy["categories"],
                    "policyChecks": policy["policyChecks"],
                },
            )
            conn.commit()
        raise HTTPException(
            status_code=400,
            detail={
                "code": "image_prompt_requires_review",
                "message": "Image prompt requires review before a provider call.",
                "userAction": "Use a generic ideation-only prompt without public figures, protected marks, final-asset wording, or sensitive claims.",
                "categories": policy["categories"],
                "policyChecks": policy["policyChecks"],
                "rightsStatus": policy["rightsStatus"],
                "safetyStatus": policy["safetyStatus"],
            },
        )
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO image_jobs
            (job_id, client_request_id, idempotency_key, tenant_id, brand_id, profile_id, user_id, prompt, status, get_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("job_img_001", request.clientRequestId, idempotency_key, request.tenantId, request.brandId, request.profileId, "usr_maya", request.prompt, "queued", 0, NOW),
        )
        insert_audit(conn, "audit_img_job_001", "image_job_created", "job_img_001", payload={"layerId": request.layer.layerId})
        conn.commit()
    return {"requestId": "req_img_001", "jobId": "job_img_001", "status": "queued", "pollAfterMs": 1000}


def get_image_job(job_id: str, request: Request) -> dict[str, Any]:
    with connect() as conn:
        job = conn.execute("SELECT * FROM image_jobs WHERE job_id = ?", (job_id,)).fetchone()
        if not job:
            raise HTTPException(status_code=404, detail={"code": "job_not_found", "message": "Image job was not found."})
        get_count = int(job["get_count"]) + 1
        status = "queued" if get_count == 1 else "running" if get_count == 2 else "completed"
        conn.execute("UPDATE image_jobs SET get_count = ?, status = ? WHERE job_id = ?", (get_count, status, job_id))
        if status == "completed":
            png = generate_placeholder_png()
            conn.execute(
                """
                INSERT OR IGNORE INTO assets
                (asset_id, job_id, width, height, placeholder_only, rights_status, safety_status, policy_checks_json, content_type, bytes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("asset_img_001", job_id, 1024, 1024, 1, "ideation_only", "passed", json.dumps(IMAGE_POLICY_CHECKS), "image/png", png, NOW),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO usage_events
                (usage_event_id, operation_id, user_id, tenant_id, brand_id, operation_type, estimated_cost_usd, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("usage_img_001", job_id, "usr_maya", job["tenant_id"], job["brand_id"], "image", 0.015, NOW),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO model_invocations
                (invocation_id, operation_id, provider, model, latency_ms, input_units, output_units, estimated_cost_usd, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("invoke_image_001", job_id, "mock-provider", MODEL, 1300, 120, 1, 0.015, NOW),
            )
            insert_audit(conn, "audit_image_completed_001", "image_job_completed", job_id, "usage_img_001", {"assetId": "asset_img_001"})
            conn.execute("UPDATE image_jobs SET usage_event_id = ?, asset_id = ? WHERE job_id = ?", ("usage_img_001", "asset_img_001", job_id))
        conn.commit()

    response: dict[str, Any] = {"jobId": job_id, "status": status}
    if status == "completed":
        asset_url = f"{str(request.base_url).rstrip('/')}/assets/asset_img_001.png"
        response["asset"] = {
            "assetId": "asset_img_001",
            "url": asset_url,
            "previewUrl": asset_url,
            "width": 1024,
            "height": 1024,
            "placeholderOnly": True,
            "rightsStatus": "ideation_only",
            "safetyStatus": "passed",
            "policyChecks": IMAGE_POLICY_CHECKS,
            "contentType": "image/png",
        }
        response["usageEventId"] = "usage_img_001"
        response["usage"] = {"usageEventId": "usage_img_001", "estimatedCostUsd": "0.015"}
    return {"requestId": "req_img_002", **response}


def get_asset_png(asset_id: str) -> bytes:
    with connect() as conn:
        asset = conn.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,)).fetchone()
        if not asset:
            raise HTTPException(status_code=404, detail={"code": "asset_not_found", "message": "Asset was not found."})
        return asset["bytes"]

