from __future__ import annotations

import importlib
import os
from pathlib import Path

from fastapi.testclient import TestClient


def client(tmp_path: Path) -> TestClient:
    os.environ["POC_DB_PATH"] = str(tmp_path / "test.sqlite")
    module = importlib.import_module("app.main")
    return TestClient(module.app)


def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer demo_plugin_session"}


def admin_headers() -> dict[str, str]:
    return {"X-Admin-Token": "demo_admin_session"}


def model_headers() -> dict[str, str]:
    return auth_headers() | {"Idempotency-Key": "idem-test"}


def copy_payload() -> dict:
    return {
        "clientRequestId": "client_copy_001",
        "contractVersion": "2026-05-poc",
        "pluginVersion": "0.1.0",
        "tenantId": "tenant_designtechco",
        "brandId": "brand_nova",
        "profileId": "profile_nova_v3",
        "campaign": "Spring Launch",
        "channel": "mobile",
        "variantCount": 3,
        "layers": [
            {"layerId": "txt_headline", "text": "Run further with gear built for spring."},
            {"layerId": "txt_cta", "text": "Shop the drop"},
        ],
    }


def localization_payload() -> dict:
    return {
        "clientRequestId": "client_loc_001",
        "contractVersion": "2026-05-poc",
        "pluginVersion": "0.1.0",
        "tenantId": "tenant_designtechco",
        "brandId": "brand_nova",
        "profileId": "profile_nova_v3",
        "channel": "mobile",
        "locales": ["fr-FR", "de-DE", "es-ES", "pt-BR", "it-IT", "nl-NL", "ja-JP", "ko-KR"],
        "layers": [{"layerId": "txt_cta", "text": "Shop the drop"}],
    }


def image_payload() -> dict:
    return {
        "clientRequestId": "client_img_001",
        "contractVersion": "2026-05-poc",
        "pluginVersion": "0.1.0",
        "tenantId": "tenant_designtechco",
        "brandId": "brand_nova",
        "profileId": "profile_nova_v3",
        "channel": "mobile",
        "layer": {
            "layerId": "img_hero",
            "type": "imageFill",
            "name": "Hero Product Placeholder",
            "dimensions": {"width": 1024, "height": 1024},
        },
        "prompt": "Lightweight running shoe on a bright spring track",
    }


def simple_pdf_bytes(*lines: str) -> bytes:
    escaped_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    text_ops = ["BT", "/F1 12 Tf", "72 720 Td"]
    for index, line in enumerate(escaped_lines):
        if index:
            text_ops.append("0 -18 Td")
        text_ops.append(f"({line}) Tj")
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    chunks = [b"%PDF-1.4\n"]
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(sum(len(chunk) for chunk in chunks))
        chunks.append(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref_offset = sum(len(chunk) for chunk in chunks)
    xref = [b"xref\n0 6\n0000000000 65535 f \n"]
    xref.extend(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    trailer = f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode()
    return b"".join(chunks + xref + [trailer])


def test_auth_context_selection_and_profile(tmp_path: Path) -> None:
    api = client(tmp_path)
    assert api.get("/health").json()["requestId"] == "req_health_001"

    unauthorized = api.get("/me/context")
    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"]["code"] == "unauthorized"

    contract_mismatch = api.post(
        "/plugin/copy/generate",
        headers=auth_headers(),
        json={**copy_payload(), "contractVersion": "2025-01-poc"},
    )
    assert contract_mismatch.status_code == 400
    assert contract_mismatch.json()["error"]["code"] == "contract_mismatch"

    start = api.post("/auth/plugin/start", json={"localNonce": "demo_nonce"}).json()
    assert start["requestId"] == "auth_req_demo"
    assert start["state"] == "state_demo"
    assert start["codeChallengeMethod"] == "S256"
    bad_exchange = api.post(
        "/auth/plugin/exchange",
        json={"requestId": "auth_req_demo", "localNonce": "demo_nonce", "codeVerifier": "wrong_verifier"},
    )
    assert bad_exchange.status_code == 400
    assert bad_exchange.json()["error"]["message"] == "PKCE verifier did not match the auth request."
    exchange = api.post("/auth/plugin/exchange", json={"requestId": "auth_req_demo", "localNonce": "demo_nonce"}).json()
    assert exchange["session"]["accessToken"] == "demo_plugin_session"
    assert exchange["session"]["tokenType"] == "Bearer"
    assert exchange["oauth"]["pkceVerified"] is True
    assert exchange["oauth"]["idTokenIssued"] is True
    assert exchange["idToken"].count(".") == 2

    context = api.get("/me/context", headers=auth_headers()).json()
    assert context["requestId"] == "req_context_001"
    assert context["tenant"]["tenantId"] == "tenant_designtechco"
    assert context["user"]["userId"] == "usr_maya"
    assert context["brands"][0]["brandId"] == "brand_nova"
    assert context["tenants"][0]["brands"][0]["enabledOperations"] == ["copy_variants", "localize", "image_placeholder"]

    selection = api.get("/fixtures/figma-selection").json()
    assert len([layer for layer in selection["layers"] if layer["type"] == "text"]) >= 2
    assert len([layer for layer in selection["layers"] if layer["type"] == "imageFill"]) == 1

    unsupported = api.post(
        "/tenants/tenant_designtechco/brands/brand_nova/guidelines",
        headers=auth_headers(),
        files={"file": ("brand-guideline-sample.png", b"not-an-allowed-type", "image/png")},
    )
    assert unsupported.status_code == 400
    assert unsupported.json()["error"]["code"] == "unsupported_file_type"

    upload = api.post(
        "/tenants/tenant_designtechco/brands/brand_nova/guidelines",
        headers=auth_headers(),
        files={"file": ("brand-guideline-sample.md", b"# Demo\nClear energetic copy.", "text/markdown")},
    ).json()
    assert upload["profileId"] == "profile_nova_v3"
    assert upload["requestId"] == "req_guideline_001"

    profiles = api.get("/tenants/tenant_designtechco/brands/brand_nova/profiles", headers=auth_headers()).json()
    assert profiles["requestId"] == "req_profiles_list_001"
    assert profiles["profiles"][0]["profileVersionId"] == "profile_nova_v3"
    assert profiles["profiles"][0]["isActive"] is True

    profile = api.get(
        "/tenants/tenant_designtechco/brands/brand_nova/profiles/profile_nova_v3",
        headers=auth_headers(),
    ).json()
    assert profile["requestId"] == "req_profile_001"
    assert profile["profileVersionId"] == "profile_nova_v3"
    assert profile["confidence"] == "high"
    assert profile["profile"]["visualNotes"] == ["Use bright ecommerce lifestyle placeholder imagery."]

    approval = api.post(
        "/tenants/tenant_designtechco/brands/brand_nova/profiles/profile_nova_v3/approve",
        headers=auth_headers(),
        json={"approved": True, "makeActive": True, "reviewComment": "Approved for pilot copy and placeholder generation."},
    ).json()
    assert approval["requestId"] == "req_profile_approve_001"
    assert approval["status"] == "active"


def test_real_pdf_extraction_and_multi_tenant_admin_operations(tmp_path: Path) -> None:
    api = client(tmp_path)

    blocked = api.get("/admin/tenants")
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "admin_required"

    tenants = api.get("/admin/tenants", headers=admin_headers()).json()
    tenant_ids = {tenant["tenantId"] for tenant in tenants["tenants"]}
    assert {"tenant_designtechco", "tenant_studioarc"}.issubset(tenant_ids)
    assert all(tenant["brands"] for tenant in tenants["tenants"])

    created_tenant = api.post(
        "/admin/tenants",
        headers=admin_headers(),
        json={"tenantId": "tenant_pilotco", "name": "Pilot Co"},
    ).json()
    assert created_tenant["status"] == "ready"

    created_brand = api.post(
        "/admin/tenants/tenant_pilotco/brands",
        headers=admin_headers(),
        json={"brandId": "brand_stride", "name": "Stride Lab"},
    ).json()
    assert created_brand["tenantId"] == "tenant_pilotco"
    assert created_brand["brandId"] == "brand_stride"

    isolated = api.get("/tenants/tenant_pilotco/brands/brand_nova/profiles", headers=auth_headers())
    assert isolated.status_code == 403
    assert isolated.json()["error"]["code"] == "unauthorized_brand"

    pdf = simple_pdf_bytes(
        "Nova Athletics Brand Guidelines",
        "Energetic clear performance-led tone.",
        "Avoid cheap and miracle claims.",
        "Use bright ecommerce lifestyle placeholder imagery.",
    )
    uploaded = api.post(
        "/tenants/tenant_designtechco/brands/brand_nova/guidelines",
        headers=auth_headers(),
        files={"file": ("brand-guideline-sample.pdf", pdf, "application/pdf")},
    ).json()
    assert uploaded["extraction"]["extractor"] == "pypdf"
    assert uploaded["extraction"]["pageCount"] == 1
    assert uploaded["extraction"]["lowConfidence"] is False
    assert uploaded["extractedCharacters"] >= 80


def test_model_operations_image_job_asset_apply_and_report(tmp_path: Path) -> None:
    api = client(tmp_path)
    quality = api.post("/quality/model-gateway/evaluate", headers=auth_headers()).json()
    assert quality["qualityRunId"] == "quality_run_001"
    assert quality["provider"] == "mock-provider"
    assert quality["model"] == "mock-gpt-4o-equivalent"
    assert quality["threshold"] == 0.9
    assert quality["score"] >= quality["threshold"]
    assert quality["passed"] is True
    assert quality["sampleCount"] == 3
    assert {result["operationType"] for result in quality["results"]} == {"copy", "localization"}
    assert all(result["passed"] for result in quality["results"])
    assert quality["qualityGate"]["goldenSampleSet"] == "project/poc/fixtures/golden-samples.json"

    copy_response = api.post("/plugin/copy/generate", headers=model_headers(), json=copy_payload()).json()
    assert copy_response["operationId"] == "op_copy_001"
    assert copy_response["requestId"] == "req_copy_001"
    assert copy_response["status"] == "completed"
    assert len(copy_response["results"]) == 2
    assert all(len(result["variants"]) == 3 for result in copy_response["results"])

    copy_repeat = api.post("/plugin/copy/generate", headers=model_headers(), json=copy_payload()).json()
    assert copy_repeat["usageEventId"] == "usage_copy_001"

    localization = api.post("/plugin/copy/localize", headers=model_headers(), json=localization_payload()).json()
    assert localization["operationId"] == "op_loc_001"
    assert len(localization["results"][0]["localizations"]) == 8
    assert localization["results"][0]["localizations"][6]["locale"] == "ja-JP"
    assert localization["results"][0]["localizations"][6]["warning"] is not None

    unsupported_locale = api.post(
        "/plugin/copy/localize",
        headers=model_headers(),
        json={**localization_payload(), "locales": ["en-US"]},
    )
    assert unsupported_locale.status_code == 400
    assert unsupported_locale.json()["error"]["code"] == "unsupported_locale"
    assert unsupported_locale.json()["error"]["details"]["unsupportedLocales"] == ["en-US"]

    blocked_image = api.post(
        "/plugin/images/jobs",
        headers=model_headers(),
        json={
            **image_payload(),
            "clientRequestId": "client_img_blocked_001",
            "prompt": "Public figure wearing a protected logo for a final campaign ad",
        },
    )
    assert blocked_image.status_code == 400
    blocked_error = blocked_image.json()["error"]
    assert blocked_error["code"] == "image_prompt_requires_review"
    assert blocked_error["category"] == "policy"
    assert blocked_error["details"]["rightsStatus"] == "ideation_only"
    assert blocked_error["details"]["safetyStatus"] == "requires_review"
    assert blocked_error["details"]["categories"] == [
        "public_figure_or_likeness",
        "protected_mark",
        "publication_or_final_asset",
    ]

    created = api.post("/plugin/images/jobs", headers=model_headers(), json=image_payload()).json()
    assert created["requestId"] == "req_img_001"
    assert created["jobId"] == "job_img_001"
    assert created["status"] == "queued"
    assert created["pollAfterMs"] == 1000
    statuses = [api.get("/plugin/images/jobs/job_img_001", headers=auth_headers()).json() for _ in range(3)]
    assert [status["status"] for status in statuses] == ["queued", "running", "completed"]
    assert statuses[-1]["asset"]["assetId"] == "asset_img_001"
    assert statuses[-1]["asset"]["placeholderOnly"] is True
    assert statuses[-1]["asset"]["rightsStatus"] == "ideation_only"
    assert statuses[-1]["asset"]["safetyStatus"] == "passed"
    assert statuses[-1]["asset"]["policyChecks"] == [
        "placeholder_only",
        "ideation_only",
        "no_public_figure",
        "no_protected_mark",
        "no_final_asset_claim",
    ]
    assert statuses[-1]["asset"]["url"].startswith("http://testserver/")
    assert statuses[-1]["requestId"] == "req_img_002"

    asset = api.get("/assets/asset_img_001.png")
    assert asset.headers["content-type"] == "image/png"
    assert asset.content.startswith(b"\x89PNG\r\n\x1a\n")

    missing_asset = api.get("/assets/missing_asset.png")
    assert missing_asset.status_code == 404
    assert missing_asset.json()["error"]["code"] == "asset_not_found"

    apply_response = api.post(
        "/plugin/apply-events",
        headers=auth_headers(),
        json={
            "operationId": "op_copy_001",
            "appliedBy": "usr_maya",
            "appliedItems": [{"layerId": "txt_headline", "outputId": "v1", "outputType": "copy"}],
        },
    ).json()
    assert apply_response["requestId"] == "req_apply_001"
    assert apply_response["applyEventId"] == "apply_001"
    assert apply_response["auditEventId"] == "audit_apply_001"
    assert apply_response["status"] == "recorded"

    image_apply_response = api.post(
        "/plugin/apply-events",
        headers=auth_headers(),
        json={
            "operationId": "job_img_001",
            "appliedBy": "usr_maya",
            "appliedItems": [{"layerId": "img_hero", "outputId": "asset_img_001", "outputType": "image"}],
        },
    ).json()
    assert image_apply_response["requestId"] == "req_apply_002"
    assert image_apply_response["applyEventId"] == "apply_002"
    assert image_apply_response["auditEventId"] == "audit_apply_002"
    assert image_apply_response["status"] == "recorded"

    report = api.get("/reports/usage", headers=auth_headers()).json()
    assert report["requestId"] == "req_usage_001"
    assert report["summary"]["operationCount"] == 3
    assert report["summary"]["appliedCount"] == 2
    assert report["summary"]["copyOperations"] == 1
    assert report["summary"]["localizationOperations"] == 1
    assert report["summary"]["imageJobs"] == 1
    assert report["summary"]["applyEvents"] == 2
    assert report["summary"]["totalOperations"] == 5
    assert report["byUser"][0]["operations"] == 3
    assert len(report["recentAuditEvents"]) >= 4
