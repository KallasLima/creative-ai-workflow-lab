from __future__ import annotations

import json
import base64
import hashlib
import hmac
from collections import Counter
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from .db import FIXTURES, connect, insert_audit
from .png import generate_placeholder_png

CONTRACT_VERSION = "2026-05-poc"
PLUGIN_VERSION = "0.1.0"
SESSION_TOKEN = "demo_plugin_session"
ADMIN_TOKEN = "demo_admin_session"
DEMO_CODE_VERIFIER = "demo_code_verifier"
DEMO_CODE_CHALLENGE = base64.urlsafe_b64encode(hashlib.sha256(DEMO_CODE_VERIFIER.encode()).digest()).rstrip(b"=").decode()
ID_TOKEN_SECRET = b"local-poc-sso-secret"
NOW = "2026-05-23T12:00:00Z"
MODEL = "mock-gpt-4o-equivalent"
LOCALES = ["fr-FR", "de-DE", "es-ES", "pt-BR", "it-IT", "nl-NL", "ja-JP", "ko-KR"]
IMAGE_POLICY_CHECKS = ["placeholder_only", "ideation_only", "no_public_figure", "no_protected_mark", "no_final_asset_claim"]
IMAGE_PROMPT_BLOCKS: list[tuple[str, tuple[str, ...]]] = [
    ("public_figure_or_likeness", ("public figure", "celebrity", "famous person", "likeness")),
    ("protected_mark", ("protected logo", "trademark", "brand logo", "competitor logo")),
    ("publication_or_final_asset", ("final campaign", "publication-ready", "final asset", "ready to publish")),
    ("sensitive_claim", ("medical claim", "political endorsement", "before and after")),
]

app = FastAPI(title="Creative AI Workflow Slice", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"^(https://.*\.figma\.com|null)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error_response(
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


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
    request_id = request.headers.get("x-request-id", "req_error")
    return _error_response(
        request_id,
        detail.get("code", f"http_{exc.status_code}"),
        detail.get("message", "Request failed."),
        exc.status_code,
        retryable=bool(detail.get("retryable", False)),
        user_action=detail.get("userAction"),
        details={k: v for k, v in detail.items() if k not in {"code", "message", "retryable", "userAction"}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        request.headers.get("x-request-id", "req_error"),
        "validation_error",
        "Request validation failed.",
        422,
        details={"errors": exc.errors()},
    )


def require_auth(authorization: Annotated[str | None, Header()] = None) -> None:
    if authorization != f"Bearer {SESSION_TOKEN}":
        raise HTTPException(status_code=401, detail={"code": "unauthorized", "message": "Valid plugin session required."})


def require_admin(x_admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None) -> None:
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail={"code": "admin_required", "message": "Admin session required."})


def pkce_challenge(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def evaluate_image_prompt_policy(prompt: str) -> dict[str, Any]:
    normalized = " ".join(prompt.lower().split())
    categories = [category for category, terms in IMAGE_PROMPT_BLOCKS if any(term in normalized for term in terms)]
    return {
        "allowed": not categories,
        "categories": categories,
        "policyChecks": IMAGE_POLICY_CHECKS,
        "rightsStatus": "ideation_only",
        "safetyStatus": "passed" if not categories else "requires_review",
    }


def b64url_json(payload: dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=").decode()


def sign_id_token(payload: dict[str, Any]) -> str:
    header = b64url_json({"alg": "HS256", "typ": "JWT"})
    body = b64url_json(payload)
    signature = hmac.new(ID_TOKEN_SECRET, f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def require_versions(contract_version: str, plugin_version: str) -> None:
    if contract_version != CONTRACT_VERSION or plugin_version != PLUGIN_VERSION:
        raise HTTPException(status_code=400, detail={"code": "contract_mismatch", "message": "Unsupported contract or plugin version."})


def require_scope(tenant_id: str, brand_id: str, profile_id: str | None = None) -> None:
    with connect() as conn:
        brand = conn.execute("SELECT * FROM brands WHERE tenant_id = ? AND brand_id = ?", (tenant_id, brand_id)).fetchone()
        if not brand:
            raise HTTPException(status_code=403, detail={"code": "unauthorized_brand", "message": "Brand is not available for this tenant."})
        if profile_id:
            profile = conn.execute("SELECT * FROM brand_profiles WHERE brand_id = ? AND profile_id = ?", (brand_id, profile_id)).fetchone()
            if not profile:
                raise HTTPException(status_code=404, detail={"code": "profile_not_found", "message": "Brand profile was not found."})


def _brand_profile_response(profile_row: Any, *, request_id: str = "req_profile_001") -> dict[str, Any]:
    tone = json.loads(profile_row["tone_json"])
    banned_phrases = json.loads(profile_row["banned_phrases_json"])
    locale_notes = json.loads(profile_row["locale_notes_json"])
    visual_notes = json.loads(profile_row["visual_notes_json"])
    review_notes = json.loads(profile_row["review_notes_json"])
    return {
        "requestId": request_id,
        "profileVersionId": profile_row["profile_id"],
        "profileId": profile_row["profile_id"],
        "brandId": profile_row["brand_id"],
        "status": profile_row["status"],
        "confidence": profile_row["confidence"],
        "version": profile_row["version"],
        "sourceGuidelineId": profile_row["source_guideline_id"],
        "sourceGuidelineIds": [profile_row["source_guideline_id"]],
        "profile": {
            "tone": tone,
            "bannedPhrases": banned_phrases,
            "localeNotes": {"fr-FR": locale_notes} if locale_notes else {},
            "visualNotes": visual_notes,
        },
        "reviewNotes": review_notes,
        "tone": tone,
        "bannedPhrases": banned_phrases,
        "updatedAt": profile_row["updated_at"],
    }


def _usage_summary(conn: Any) -> dict[str, Any]:
    usage_rows = conn.execute("SELECT operation_type, estimated_cost_usd, user_id FROM usage_events").fetchall()
    counts = Counter(row["operation_type"] for row in usage_rows)
    by_user_operation: dict[tuple[str, str], dict[str, Any]] = {}
    cost_by_user: dict[str, dict[str, Any]] = {}
    for row in usage_rows:
        bucket = cost_by_user.setdefault(row["user_id"], {"operations": 0, "estimatedCostUsd": 0.0})
        bucket["operations"] += 1
        bucket["estimatedCostUsd"] = round(bucket["estimatedCostUsd"] + float(row["estimated_cost_usd"]), 3)
        op_bucket = by_user_operation.setdefault(
            (row["user_id"], row["operation_type"]),
            {
                "userId": row["user_id"],
                "brandId": "brand_nova",
                "operationType": row["operation_type"],
                "operationCount": 0,
                "estimatedCostUsd": 0.0,
            },
        )
        op_bucket["operationCount"] += 1
        op_bucket["estimatedCostUsd"] = round(op_bucket["estimatedCostUsd"] + float(row["estimated_cost_usd"]), 3)
    audit_rows = conn.execute(
        "SELECT audit_event_id, type, operation_id, usage_event_id, created_at FROM audit_events ORDER BY created_at DESC, audit_event_id DESC LIMIT 10"
    ).fetchall()
    apply_count = conn.execute("SELECT COUNT(*) AS c FROM apply_events").fetchone()["c"]
    total_operations = len(usage_rows) + int(apply_count)
    return {
        "summary": {
            "operationCount": len(usage_rows),
            "appliedCount": int(apply_count),
            "estimatedCostUsd": round(sum(float(row["estimated_cost_usd"]) for row in usage_rows), 3),
            "medianTextLatencyMs": 610,
            "imageJobFailureRate": 0.0,
            "totalOperations": total_operations,
            "totalEstimatedCostUsd": round(sum(float(row["estimated_cost_usd"]) for row in usage_rows), 3),
            "copyOperations": counts.get("copy", 0),
            "localizationOperations": counts.get("localization", 0),
            "imageJobs": counts.get("image", 0),
            "applyEvents": int(apply_count),
        },
        "groups": list(by_user_operation.values()),
        "byUser": [
            {
                "userId": user_id,
                "displayName": "Maya Chen",
                "operations": bucket["operations"],
                "estimatedCostUsd": bucket["estimatedCostUsd"],
            }
            for user_id, bucket in cost_by_user.items()
        ],
        "recentAuditEvents": [
            {
                "auditEventId": row["audit_event_id"],
                "type": row["type"],
                "operationId": row["operation_id"],
                "usageEventId": row["usage_event_id"],
                "createdAt": row["created_at"],
            }
            for row in audit_rows
        ],
    }


def _copy_variants_for_layer(layer_id: str) -> list[dict[str, Any]]:
    if layer_id == "txt_cta":
        return [
            {"variantId": "v1", "text": "Shop spring gear", "score": 0.9},
            {"variantId": "v2", "text": "Find your run kit", "score": 0.87},
            {"variantId": "v3", "text": "Start your spring run", "score": 0.85},
        ]
    return [
        {"variantId": "v1", "text": "Spring miles start with gear that keeps up.", "score": 0.91},
        {"variantId": "v2", "text": "Built for longer runs and brighter days.", "score": 0.88},
        {"variantId": "v3", "text": "Your spring run kit, ready for every mile.", "score": 0.86},
    ]


def _localized_text_by_locale() -> dict[str, str]:
    return {
        "fr-FR": "Découvrir la collection",
        "de-DE": "Kollektion shoppen",
        "es-ES": "Compra la colección",
        "pt-BR": "Compre a coleção",
        "it-IT": "Scopri la collezione",
        "nl-NL": "Shop de collectie",
        "ja-JP": "コレクションを見る",
        "ko-KR": "컬렉션 쇼핑하기",
    }


def _score_checks(checks: list[dict[str, Any]]) -> tuple[float, bool]:
    if not checks:
        return 0.0, False
    passed = sum(1 for check in checks if check["passed"])
    score = round(passed / len(checks), 3)
    return score, passed == len(checks)


def _evaluate_copy_sample(sample: dict[str, Any]) -> dict[str, Any]:
    variants = _copy_variants_for_layer(sample["layerId"])
    best_text = variants[0]["text"]
    lower_text = best_text.lower()
    banned = [phrase for phrase in sample.get("bannedPhrases", []) if phrase.lower() in lower_text]
    missing_terms = [term for term in sample.get("requiredTerms", []) if term.lower() not in lower_text]
    checks = [
        {"name": "schema_valid", "passed": all("variantId" in variant and "text" in variant and "score" in variant for variant in variants)},
        {"name": "required_terms_present", "passed": not missing_terms, "missingTerms": missing_terms},
        {"name": "banned_phrases_absent", "passed": not banned, "bannedPhrasesFound": banned},
        {"name": "max_length_respected", "passed": len(best_text) <= int(sample["maxCharacters"]), "characters": len(best_text)},
    ]
    score, passed = _score_checks(checks)
    return {
        "sampleId": sample["sampleId"],
        "operationType": "copy",
        "score": score,
        "passed": passed,
        "checks": checks,
        "outputPreview": best_text,
    }


def _evaluate_localization_sample(sample: dict[str, Any]) -> dict[str, Any]:
    locale_text = _localized_text_by_locale()
    required = sample.get("requiredLocales", [])
    outputs = [{"locale": locale, "text": locale_text[locale]} for locale in required if locale in locale_text]
    joined = " ".join(output["text"].lower() for output in outputs)
    banned = [phrase for phrase in sample.get("bannedPhrases", []) if phrase.lower() in joined]
    over_limit = [output["locale"] for output in outputs if len(output["text"]) > int(sample["maxCharacters"])]
    checks = [
        {"name": "schema_valid", "passed": all("locale" in output and "text" in output for output in outputs)},
        {"name": "locale_coverage", "passed": len(outputs) == len(required), "expected": len(required), "actual": len(outputs)},
        {"name": "banned_phrases_absent", "passed": not banned, "bannedPhrasesFound": banned},
        {"name": "max_length_respected", "passed": not over_limit, "overLimitLocales": over_limit},
    ]
    score, passed = _score_checks(checks)
    return {
        "sampleId": sample["sampleId"],
        "operationType": "localization",
        "score": score,
        "passed": passed,
        "checks": checks,
        "outputPreview": json.dumps(outputs, ensure_ascii=False),
    }


def _run_quality_gate() -> dict[str, Any]:
    fixture = json.loads((FIXTURES / "golden-samples.json").read_text())
    results = []
    for sample in fixture["samples"]:
        if sample["operationType"] == "copy":
            results.append(_evaluate_copy_sample(sample))
        elif sample["operationType"] == "localization":
            results.append(_evaluate_localization_sample(sample))
        else:
            raise HTTPException(status_code=400, detail={"code": "quality_gate_failed", "message": "Unsupported golden sample operation."})
    aggregate = round(sum(result["score"] for result in results) / len(results), 3)
    passed = aggregate >= float(fixture["threshold"]) and all(result["passed"] for result in results)
    return {
        "requestId": "req_quality_001",
        "qualityRunId": "quality_run_001",
        "provider": fixture["provider"],
        "model": fixture["model"],
        "threshold": fixture["threshold"],
        "score": aggregate,
        "passed": passed,
        "sampleCount": len(results),
        "results": results,
    }


class AuthStartRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    pluginVersion: str = PLUGIN_VERSION
    contractVersion: str = CONTRACT_VERSION
    localNonce: str = "demo_nonce"
    state: str = "state_demo"
    codeChallenge: str = DEMO_CODE_CHALLENGE
    codeChallengeMethod: Literal["S256"] = "S256"
    figmaUserHint: str | None = None


class AuthExchangeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    requestId: str
    localNonce: str
    state: str = "state_demo"
    codeVerifier: str = DEMO_CODE_VERIFIER
    pluginVersion: str = PLUGIN_VERSION
    contractVersion: str = CONTRACT_VERSION


class LayerText(BaseModel):
    model_config = ConfigDict(extra="ignore")
    layerId: str
    text: str


class CopyGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    clientRequestId: str = Field(min_length=1)
    contractVersion: str
    pluginVersion: str
    tenantId: str
    brandId: str
    profileId: str
    campaign: str
    channel: str
    variantCount: int = Field(default=3, ge=1, le=3)
    layers: list[LayerText] = Field(min_length=1)


class LocalizationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    clientRequestId: str = Field(min_length=1)
    contractVersion: str
    pluginVersion: str
    tenantId: str
    brandId: str
    profileId: str
    channel: str
    locales: list[str] = Field(min_length=1, max_length=8)
    layers: list[LayerText] = Field(min_length=1)


class ImageDimensions(BaseModel):
    model_config = ConfigDict(extra="ignore")
    width: int
    height: int


class ImageLayer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    layerId: str
    name: str
    type: Literal["imageFill"] = "imageFill"
    dimensions: ImageDimensions


class ImageJobRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    clientRequestId: str = Field(min_length=1)
    contractVersion: str
    pluginVersion: str
    tenantId: str
    brandId: str
    profileId: str
    channel: str
    layer: ImageLayer
    prompt: str


class AppliedItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    layerId: str
    outputId: str
    outputType: Literal["copy", "image"]


class ApplyEventRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    operationId: str
    appliedBy: str
    appliedItems: list[AppliedItem] = Field(min_length=1)
    generationRequestId: str | None = None
    appliedAt: str | None = None
    figmaFileKey: str | None = None
    skippedItems: list[dict[str, Any]] = Field(default_factory=list)


class ApproveProfileRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    approved: bool = True
    makeActive: bool = True
    reviewComment: str | None = None


@app.get("/health")
def health() -> dict[str, Any]:
    with connect() as conn:
        conn.execute("SELECT 1").fetchone()
    return {"requestId": "req_health_001", "status": "ok", "contractVersion": CONTRACT_VERSION, "database": "sqlite"}


@app.post("/auth/plugin/start")
def auth_start(request: AuthStartRequest) -> dict[str, Any]:
    require_versions(request.contractVersion, request.pluginVersion)
    auth_code = "oauth_code_demo"
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO plugin_auth_requests
            (request_id, local_nonce, state, code_challenge, code_challenge_method, auth_code, completed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("auth_req_demo", request.localNonce, request.state, request.codeChallenge, request.codeChallengeMethod, auth_code, 0, NOW),
        )
        insert_audit(conn, "audit_auth_start_001", "plugin_oauth_started", payload={"state": request.state, "codeChallengeMethod": request.codeChallengeMethod})
        conn.commit()
    return {
        "requestId": "auth_req_demo",
        "browserUrl": "http://localhost:5173/mock-auth/auth_req_demo",
        "state": request.state,
        "codeChallengeMethod": request.codeChallengeMethod,
        "authorizationCodeIssued": True,
        "expiresAt": "2026-05-23T23:59:00Z",
        "pollAfterMs": 500,
    }


@app.post("/auth/plugin/exchange")
def auth_exchange(request: AuthExchangeRequest) -> dict[str, Any]:
    require_versions(request.contractVersion, request.pluginVersion)
    with connect() as conn:
        auth_request = conn.execute("SELECT * FROM plugin_auth_requests WHERE request_id = ?", (request.requestId,)).fetchone()
        if not auth_request:
            raise HTTPException(status_code=400, detail={"code": "auth_request_invalid", "message": "Demo auth request was not completed."})
        if auth_request["completed"]:
            raise HTTPException(status_code=400, detail={"code": "auth_request_invalid", "message": "Auth code was already exchanged."})
        if auth_request["local_nonce"] != request.localNonce or auth_request["state"] != request.state:
            raise HTTPException(status_code=400, detail={"code": "auth_request_invalid", "message": "OAuth state or nonce did not match."})
        if pkce_challenge(request.codeVerifier) != auth_request["code_challenge"]:
            raise HTTPException(status_code=400, detail={"code": "auth_request_invalid", "message": "PKCE verifier did not match the auth request."})
        id_token = sign_id_token(
            {
                "iss": "https://auth.local.creative-ai-workflow",
                "aud": "creative-ai-workflow-figma-plugin",
                "sub": "usr_maya",
                "tenant_id": "tenant_designtechco",
                "session_id": SESSION_TOKEN,
                "nonce": request.localNonce,
                "iat": 1779556800,
                "exp": 1779609540,
            }
        )
        conn.execute("UPDATE plugin_auth_requests SET completed = 1 WHERE request_id = ?", (request.requestId,))
        conn.execute(
            """
            INSERT OR REPLACE INTO plugin_sessions
            (session_token, user_id, tenant_id, state, id_token, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (SESSION_TOKEN, "usr_maya", "tenant_designtechco", request.state, id_token, "2026-05-24T00:59:00Z", NOW),
        )
        insert_audit(conn, "audit_auth_exchange_001", "plugin_session_issued", payload={"state": request.state, "userId": "usr_maya"})
        conn.commit()

    if request.requestId != "auth_req_demo" or request.localNonce != "demo_nonce":
        raise HTTPException(status_code=400, detail={"code": "auth_request_invalid", "message": "Demo auth request was not completed."})
    return {
        "requestId": "auth_req_demo",
        "session": {"accessToken": SESSION_TOKEN, "expiresAt": "2026-05-24T00:59:00Z", "tokenType": "Bearer"},
        "oauth": {"state": request.state, "pkceVerified": True, "idTokenIssued": True},
        "idToken": id_token,
        "user": {"userId": "usr_maya", "displayName": "Maya Chen"},
    }


@app.get("/me/context", dependencies=[Depends(require_auth)])
def context() -> dict[str, Any]:
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


def extract_guideline_text(filename: str, raw: bytes) -> tuple[str, dict[str, Any]]:
    suffix = Path(filename).suffix.lower()
    if suffix != ".pdf":
        text = raw.decode("utf-8", errors="replace")
        return text, {"extractor": "utf-8", "pageCount": 1, "lowConfidence": len(text.strip()) < 40}

    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - guarded by requirements and verifier.
        raise HTTPException(
            status_code=500,
            detail={"code": "pdf_extractor_unavailable", "message": "PDF extractor dependency is unavailable."},
        ) from exc

    import io

    try:
        reader = PdfReader(io.BytesIO(raw))
        pages = [page.extract_text(extraction_mode="layout") or page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "pdf_extraction_failed", "message": "Could not extract text from the uploaded PDF.", "retryable": False},
        ) from exc

    text = "\n\n".join(page.strip() for page in pages if page.strip()).strip()
    low_confidence = len(text) < 80 or len(text) / max(len(raw), 1) < 0.01
    return text, {"extractor": "pypdf", "pageCount": len(reader.pages), "lowConfidence": low_confidence}


@app.post("/tenants/{tenant_id}/brands/{brand_id}/guidelines", dependencies=[Depends(require_auth)])
async def upload_guideline(
    tenant_id: str,
    brand_id: str,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    require_scope(tenant_id, brand_id)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".md", ".txt", ".pdf"}:
        raise HTTPException(status_code=400, detail={"code": "unsupported_file_type", "message": "Use .md, .txt, or .pdf."})

    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "file_too_large", "message": "Guideline upload must be <= 10 MB."})

    extracted, extraction = extract_guideline_text(file.filename or "uploaded-guideline", raw)
    if not extracted.strip():
        raise HTTPException(status_code=400, detail={"code": "pdf_extraction_failed", "message": "Uploaded guideline did not produce usable text."})

    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO brand_guidelines
            (guideline_id, tenant_id, brand_id, source_name, size_bytes, extracted_characters, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("guide_nova_001", tenant_id, brand_id, file.filename or "uploaded-guideline", len(raw), len(extracted), extracted, NOW),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO brand_profiles
            (profile_id, brand_id, status, confidence, version, source_guideline_id, tone_json, banned_phrases_json, locale_notes_json, visual_notes_json, review_notes_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "profile_nova_v3",
                brand_id,
                "approved",
                "high",
                3,
                "guide_nova_001",
                json.dumps(["energetic", "clear", "performance-led"]),
                json.dumps(["cheap", "miracle"]),
                json.dumps(["Preserve concise CTA style across locales"]),
                json.dumps(["Use bright ecommerce lifestyle placeholder imagery."]),
                json.dumps([]),
                NOW,
            ),
        )
        insert_audit(conn, "audit_guideline_001", "brand_guideline_profile_approved", payload={"sourceName": file.filename})
        conn.commit()

    return {
        "requestId": "req_guideline_001",
        "guidelineId": "guide_nova_001",
        "profileId": "profile_nova_v3",
        "status": "approved",
        "sizeBytes": len(raw),
        "extractedCharacters": len(extracted),
        "extraction": extraction,
        "profile": {
            "tone": ["energetic", "clear", "performance-led"],
            "bannedPhrases": ["cheap", "miracle"],
            "localeNotes": ["Preserve concise CTA style across locales"],
            "visualNotes": ["Use bright ecommerce lifestyle placeholder imagery."],
        },
    }


class TenantCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    tenantId: str = Field(pattern=r"^tenant_[a-z0-9_]+$")
    name: str = Field(min_length=2)


class BrandCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    brandId: str = Field(pattern=r"^brand_[a-z0-9_]+$")
    name: str = Field(min_length=2)


@app.get("/admin/tenants", dependencies=[Depends(require_admin)])
def admin_list_tenants() -> dict[str, Any]:
    with connect() as conn:
        tenants = conn.execute("SELECT tenant_id, name FROM tenants ORDER BY tenant_id").fetchall()
        brands = conn.execute("SELECT tenant_id, brand_id, name, active_profile_id FROM brands ORDER BY tenant_id, brand_id").fetchall()
        users = conn.execute("SELECT tenant_id, user_id, display_name, role FROM users ORDER BY tenant_id, user_id").fetchall()
    brands_by_tenant: dict[str, list[dict[str, Any]]] = {}
    for brand in brands:
        brands_by_tenant.setdefault(brand["tenant_id"], []).append(
            {
                "brandId": brand["brand_id"],
                "name": brand["name"],
                "activeProfileId": brand["active_profile_id"] or None,
            }
        )
    users_by_tenant: dict[str, list[dict[str, Any]]] = {}
    for user in users:
        users_by_tenant.setdefault(user["tenant_id"], []).append(
            {"userId": user["user_id"], "displayName": user["display_name"], "role": user["role"]}
        )
    return {
        "requestId": "req_admin_tenants_001",
        "tenants": [
            {
                "tenantId": tenant["tenant_id"],
                "name": tenant["name"],
                "brands": brands_by_tenant.get(tenant["tenant_id"], []),
                "users": users_by_tenant.get(tenant["tenant_id"], []),
            }
            for tenant in tenants
        ],
    }


@app.post("/admin/tenants", dependencies=[Depends(require_admin)])
def admin_create_tenant(payload: TenantCreateRequest) -> dict[str, Any]:
    with connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO tenants (tenant_id, name) VALUES (?, ?)",
            (payload.tenantId, payload.name),
        )
        insert_audit(conn, "audit_admin_tenant_001", "tenant_created", payload={"tenantId": payload.tenantId})
        conn.commit()
    return {"requestId": "req_admin_tenant_create_001", "tenantId": payload.tenantId, "status": "ready"}


@app.post("/admin/tenants/{tenant_id}/brands", dependencies=[Depends(require_admin)])
def admin_create_brand(tenant_id: str, payload: BrandCreateRequest) -> dict[str, Any]:
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


@app.get("/tenants/{tenant_id}/brands/{brand_id}/profiles", dependencies=[Depends(require_auth)])
def list_profiles(tenant_id: str, brand_id: str) -> dict[str, Any]:
    require_scope(tenant_id, brand_id)
    with connect() as conn:
        active_profile = conn.execute(
            "SELECT active_profile_id FROM brands WHERE tenant_id = ? AND brand_id = ?",
            (tenant_id, brand_id),
        ).fetchone()
        rows = conn.execute(
            "SELECT * FROM brand_profiles WHERE brand_id = ? ORDER BY version DESC, profile_id DESC",
            (brand_id,),
        ).fetchall()
    return {
        "requestId": "req_profiles_list_001",
        "brandId": brand_id,
        "profiles": [
            {
                "profileVersionId": row["profile_id"],
                "status": row["status"],
                "confidence": row["confidence"],
                "version": row["version"],
                "sourceGuidelineIds": [row["source_guideline_id"]],
                "isActive": row["profile_id"] == (active_profile["active_profile_id"] if active_profile else None),
            }
            for row in rows
        ],
    }


@app.get("/tenants/{tenant_id}/brands/{brand_id}/profiles/{profile_id}", dependencies=[Depends(require_auth)])
def get_profile(tenant_id: str, brand_id: str, profile_id: str) -> dict[str, Any]:
    require_scope(tenant_id, brand_id, profile_id)
    with connect() as conn:
        profile = conn.execute("SELECT * FROM brand_profiles WHERE profile_id = ?", (profile_id,)).fetchone()
    return _brand_profile_response(profile)


@app.post("/tenants/{tenant_id}/brands/{brand_id}/profiles/{profile_id}/approve", dependencies=[Depends(require_auth)])
def approve_profile(tenant_id: str, brand_id: str, profile_id: str, payload: ApproveProfileRequest) -> dict[str, Any]:
    require_scope(tenant_id, brand_id, profile_id)
    if not payload.approved or not payload.makeActive:
        raise HTTPException(status_code=400, detail={"code": "invalid_profile_approval", "message": "Approval must mark the profile active."})

    with connect() as conn:
        profile = conn.execute("SELECT * FROM brand_profiles WHERE profile_id = ? AND brand_id = ?", (profile_id, brand_id)).fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail={"code": "profile_not_found", "message": "Brand profile was not found."})
        previous_active = conn.execute("SELECT active_profile_id FROM brands WHERE brand_id = ? AND tenant_id = ?", (brand_id, tenant_id)).fetchone()
        conn.execute("UPDATE brand_profiles SET status = ?, confidence = ? WHERE profile_id = ?", ("active", profile["confidence"], profile_id))
        conn.execute("UPDATE brands SET active_profile_id = ? WHERE brand_id = ? AND tenant_id = ?", (profile_id, brand_id, tenant_id))
        insert_audit(
            conn,
            "audit_profile_approve_001",
            "brand_profile_approved",
            operation_id=profile_id,
            payload={"reviewComment": payload.reviewComment or "", "makeActive": True},
        )
        conn.commit()

    return {
        "requestId": "req_profile_approve_001",
        "profileVersionId": profile_id,
        "status": "active",
        "previousActiveProfileVersionId": previous_active["active_profile_id"] if previous_active else None,
    }


@app.get("/fixtures/figma-selection")
def figma_selection() -> dict[str, Any]:
    return json.loads((FIXTURES / "figma-selection.json").read_text())


def _record_operation(
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


@app.post("/plugin/copy/generate", dependencies=[Depends(require_auth)])
def copy_generate(request: CopyGenerateRequest, idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None) -> dict[str, Any]:
    require_versions(request.contractVersion, request.pluginVersion)
    require_scope(request.tenantId, request.brandId, request.profileId)
    if request.variantCount > 3:
        raise HTTPException(status_code=400, detail={"code": "invalid_copy_request", "message": "variantCount must be 1-3 for the demo."})
    results = []
    for layer in request.layers:
        variants = _copy_variants_for_layer(layer.layerId)
        results.append({"layerId": layer.layerId, "variants": variants[: request.variantCount]})

    _record_operation(
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


@app.post("/plugin/copy/localize", dependencies=[Depends(require_auth)])
def copy_localize(request: LocalizationRequest, idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None) -> dict[str, Any]:
    require_versions(request.contractVersion, request.pluginVersion)
    require_scope(request.tenantId, request.brandId, request.profileId)
    if len(request.locales) > 8:
        raise HTTPException(status_code=400, detail={"code": "invalid_locale_count", "message": "Localize requests support at most 8 locales."})
    locale_text = _localized_text_by_locale()
    unsupported = [locale for locale in request.locales if locale not in locale_text]
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
    localizations = [
        {"locale": locale, "text": locale_text[locale], "warning": None if locale != "ja-JP" else "Review character width for compact CTA buttons."}
        for locale in LOCALES
        if locale in requested
    ]
    results = [{"layerId": layer.layerId, "localizations": localizations} for layer in request.layers]
    _record_operation(
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


@app.post("/quality/model-gateway/evaluate", dependencies=[Depends(require_auth)])
def model_quality_evaluate() -> dict[str, Any]:
    result = _run_quality_gate()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO model_quality_runs
            (run_id, provider, model, threshold, score, passed, sample_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["qualityRunId"],
                result["provider"],
                result["model"],
                result["threshold"],
                result["score"],
                1 if result["passed"] else 0,
                result["sampleCount"],
                NOW,
            ),
        )
        for index, sample_result in enumerate(result["results"], start=1):
            conn.execute(
                """
                INSERT OR REPLACE INTO model_quality_results
                (result_id, run_id, sample_id, operation_type, score, passed, checks_json, output_preview, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"quality_result_{index:03d}",
                    result["qualityRunId"],
                    sample_result["sampleId"],
                    sample_result["operationType"],
                    sample_result["score"],
                    1 if sample_result["passed"] else 0,
                    json.dumps(sample_result["checks"], ensure_ascii=False),
                    sample_result["outputPreview"],
                    NOW,
                ),
            )
        insert_audit(
            conn,
            "audit_quality_gate_001",
            "model_quality_gate_completed",
            operation_id=result["qualityRunId"],
            payload={"provider": result["provider"], "model": result["model"], "score": result["score"], "passed": result["passed"]},
        )
        conn.commit()
    return {
        **result,
        "qualityGate": {
            "goldenSampleSet": "project/poc/fixtures/golden-samples.json",
            "proves": "Executable provider-quality gate mechanics against local golden samples.",
            "doesNotProve": "Live paid or approved model-provider quality in a production environment.",
        },
    }


@app.post("/plugin/images/jobs", dependencies=[Depends(require_auth)])
def image_job_create(request: ImageJobRequest, idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None) -> dict[str, Any]:
    require_versions(request.contractVersion, request.pluginVersion)
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


@app.get("/plugin/images/jobs/{job_id}", dependencies=[Depends(require_auth)])
def image_job_get(job_id: str, request: Request) -> dict[str, Any]:
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


@app.get("/assets/{asset_id}.png")
def asset_png(asset_id: str) -> Response:
    with connect() as conn:
        asset = conn.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,)).fetchone()
        if not asset:
            raise HTTPException(status_code=404, detail={"code": "asset_not_found", "message": "Asset was not found."})
        data = asset["bytes"]
    return Response(content=data, media_type="image/png")


@app.post("/plugin/apply-events", dependencies=[Depends(require_auth)])
def apply_event(request: ApplyEventRequest) -> dict[str, Any]:
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


@app.get("/reports/usage", dependencies=[Depends(require_auth)])
def usage_report() -> dict[str, Any]:
    with connect() as conn:
        return {"requestId": "req_usage_001", **_usage_summary(conn)}
