#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
POC="$ROOT/project/poc"
BACKEND="$POC/backend"
VENV="$BACKEND/.venv"
PY="$VENV/bin/python"
PYTHON_BIN="${PYTHON_BIN:-}"
API_URL="${API_URL:-http://127.0.0.1:8000}"
TMP_DIR=""
DB_PATH=""
LOG_FILE=""
STARTED_PID=""
LOCK_DIR="$POC/.run-lock"
LOCK_ACQUIRED="0"

find_python() {
  if [ -n "$PYTHON_BIN" ]; then
    if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
      command -v "$PYTHON_BIN"
      return
    fi
    echo "[verify-api] PYTHON_BIN is set but was not found: $PYTHON_BIN" >&2
    exit 1
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi
  echo "[verify-api] python3 or python is required" >&2
  exit 1
}

acquire_lock() {
  if [ "${POC_LOCK_HELD:-0}" = "1" ]; then
    return
  fi

  if mkdir "$LOCK_DIR" 2>/dev/null; then
    write_lock
    return
  fi

  if lock_is_active; then
    echo "[verify-api] another POC script is already running; wait for it to finish before running API verification" >&2
    exit 1
  fi

  echo "[verify-api] removing stale POC run lock" >&2
  rm -rf "$LOCK_DIR"
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    write_lock
    return
  fi

  echo "[verify-api] another POC script is already running; wait for it to finish before running API verification" >&2
  exit 1
}

write_lock() {
  LOCK_ACQUIRED="1"
  printf '%s\n' "$$" > "$LOCK_DIR/pid"
}

lock_is_active() {
  local owner=""

  if [ -f "$LOCK_DIR/pid" ]; then
    owner="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
  fi

  if [[ "$owner" =~ ^[0-9]+$ ]] && kill -0 "$owner" 2>/dev/null; then
    return 0
  fi

  return 1
}

port_is_free() {
  local port="${1:-}"

  "$PYTHON_BIN" - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(0.5)
try:
    sock.bind(("127.0.0.1", port))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
}

cleanup() {
  if [ -n "$STARTED_PID" ] && kill -0 "$STARTED_PID" 2>/dev/null; then
    kill "$STARTED_PID" 2>/dev/null || true
    wait "$STARTED_PID" 2>/dev/null || true
  fi
  if [ -n "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
  fi
  if [ "$LOCK_ACQUIRED" = "1" ]; then
    rm -rf "$LOCK_DIR"
  fi
}

trap cleanup EXIT
acquire_lock
PYTHON_BIN="$(find_python)"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/creative-ai-workflow-verify-api.XXXXXX")"
DB_PATH="$TMP_DIR/verify-api.sqlite"
LOG_FILE="$TMP_DIR/verify-api.log"

if [ ! -x "$PY" ]; then
  "$PYTHON_BIN" -m venv "$VENV"
fi

"$PY" -m pip install -q -r "$BACKEND/requirements.txt"

wait_for_health() {
  "$PY" - "$API_URL" <<'PY'
import sys
import time
import httpx

base_url = sys.argv[1]
for _ in range(60):
    try:
        response = httpx.get(f"{base_url}/health", timeout=1.0)
        if response.status_code == 200:
            raise SystemExit(0)
    except Exception:
        pass
    time.sleep(0.25)
raise SystemExit(1)
PY
}

if ! wait_for_health; then
  if ! port_is_free 8000; then
    echo "[verify-api] port 8000 is already in use and does not appear to be serving the local backend"
    exit 1
  fi
  echo "[verify-api] backend not reachable at $API_URL, starting local uvicorn"
  rm -f "$DB_PATH" "$LOG_FILE"
  (cd "$BACKEND" && POC_DB_PATH="$DB_PATH" "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > "$LOG_FILE" 2>&1) &
  STARTED_PID="$!"
  if ! wait_for_health; then
    echo "[verify-api] backend failed to start; log follows:"
    cat "$LOG_FILE"
    exit 1
  fi
  echo "[verify-api] backend started by verifier and will be stopped on exit"
fi

echo "[verify-api] step 1: health"
"$PY" - "$API_URL" <<'PY'
import sys
import httpx

response = httpx.get(f"{sys.argv[1]}/health", timeout=2.0)
response.raise_for_status()
payload = response.json()
assert payload["requestId"] == "req_health_001"
assert payload["status"] == "ok"
assert payload["contractVersion"] == "2026-05-poc"
print("[verify-api] health PASS")
PY

echo "[verify-api] step 2: auth and context"
"$PY" - "$API_URL" <<'PY'
import sys
import httpx

base_url = sys.argv[1]
auth = {"Authorization": "Bearer demo_plugin_session"}

start = httpx.post(f"{base_url}/auth/plugin/start", json={"localNonce": "demo_nonce"}, timeout=2.0)
start.raise_for_status()
assert start.json()["requestId"] == "auth_req_demo"
assert start.json()["state"] == "state_demo"
assert start.json()["codeChallengeMethod"] == "S256"

bad_exchange = httpx.post(
    f"{base_url}/auth/plugin/exchange",
    json={"requestId": "auth_req_demo", "localNonce": "demo_nonce", "codeVerifier": "wrong_verifier"},
    timeout=2.0,
)
assert bad_exchange.status_code == 400
assert bad_exchange.json()["error"]["message"] == "PKCE verifier did not match the auth request."

exchange = httpx.post(
    f"{base_url}/auth/plugin/exchange",
    json={"requestId": "auth_req_demo", "localNonce": "demo_nonce"},
    timeout=2.0,
)
exchange.raise_for_status()
assert exchange.json()["session"]["accessToken"] == "demo_plugin_session"
assert exchange.json()["session"]["tokenType"] == "Bearer"
assert exchange.json()["oauth"]["pkceVerified"] is True
assert exchange.json()["oauth"]["idTokenIssued"] is True
assert exchange.json()["idToken"].count(".") == 2

context = httpx.get(f"{base_url}/me/context", headers=auth, timeout=2.0)
context.raise_for_status()
payload = context.json()
assert payload["requestId"] == "req_context_001"
assert payload["tenant"]["tenantId"] == "tenant_designtechco"
assert payload["user"]["userId"] == "usr_maya"
assert payload["brands"][0]["brandId"] == "brand_nova"
assert payload["tenants"][0]["brands"][0]["enabledOperations"] == ["copy_variants", "localize", "image_placeholder"]
print("[verify-api] auth/context PASS")
PY

echo "[verify-api] step 3: selection, real PDF extraction, admin operations, and profile governance"
"$PY" - "$API_URL" "$POC/fixtures/brand-guideline-sample.md" <<'PY'
import sys
from pathlib import Path

import httpx

base_url = sys.argv[1]
guideline = Path(sys.argv[2])
auth = {"Authorization": "Bearer demo_plugin_session"}
admin = {"X-Admin-Token": "demo_admin_session"}


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

selection = httpx.get(f"{base_url}/fixtures/figma-selection", timeout=2.0)
selection.raise_for_status()
layers = selection.json()["layers"]
assert sum(1 for layer in layers if layer["type"] == "text") >= 2
assert sum(1 for layer in layers if layer["type"] == "imageFill") == 1

unsupported = httpx.post(
    f"{base_url}/tenants/tenant_designtechco/brands/brand_nova/guidelines",
    headers=auth,
    files={"file": ("brand-guideline-sample.png", b"not-allowed", "image/png")},
    timeout=2.0,
)
assert unsupported.status_code == 400
assert unsupported.json()["error"]["code"] == "unsupported_file_type"

admin_blocked = httpx.get(f"{base_url}/admin/tenants", timeout=2.0)
assert admin_blocked.status_code == 403
assert admin_blocked.json()["error"]["code"] == "admin_required"

tenants = httpx.get(f"{base_url}/admin/tenants", headers=admin, timeout=2.0)
tenants.raise_for_status()
tenant_ids = {tenant["tenantId"] for tenant in tenants.json()["tenants"]}
assert {"tenant_designtechco", "tenant_studioarc"}.issubset(tenant_ids)

tenant_create = httpx.post(
    f"{base_url}/admin/tenants",
    headers=admin,
    json={"tenantId": "tenant_pilotco", "name": "Pilot Co"},
    timeout=2.0,
)
tenant_create.raise_for_status()
assert tenant_create.json()["status"] == "ready"

brand_create = httpx.post(
    f"{base_url}/admin/tenants/tenant_pilotco/brands",
    headers=admin,
    json={"brandId": "brand_stride", "name": "Stride Lab"},
    timeout=2.0,
)
brand_create.raise_for_status()
assert brand_create.json()["brandId"] == "brand_stride"

isolated = httpx.get(f"{base_url}/tenants/tenant_pilotco/brands/brand_nova/profiles", headers=auth, timeout=2.0)
assert isolated.status_code == 403
assert isolated.json()["error"]["code"] == "unauthorized_brand"

pdf = simple_pdf_bytes(
    "Nova Athletics Brand Guidelines",
    "Energetic clear performance-led tone.",
    "Avoid cheap and miracle claims.",
    "Use bright ecommerce lifestyle placeholder imagery.",
)
upload = httpx.post(
    f"{base_url}/tenants/tenant_designtechco/brands/brand_nova/guidelines",
    headers=auth,
    files={"file": ("brand-guideline-sample.pdf", pdf, "application/pdf")},
    timeout=2.0,
)
upload.raise_for_status()
assert upload.json()["requestId"] == "req_guideline_001"
assert upload.json()["profileId"] == "profile_nova_v3"
assert upload.json()["extraction"]["extractor"] == "pypdf"
assert upload.json()["extraction"]["pageCount"] == 1
assert upload.json()["extraction"]["lowConfidence"] is False

profiles = httpx.get(f"{base_url}/tenants/tenant_designtechco/brands/brand_nova/profiles", headers=auth, timeout=2.0)
profiles.raise_for_status()
assert profiles.json()["profiles"][0]["profileVersionId"] == "profile_nova_v3"
assert profiles.json()["profiles"][0]["isActive"] is True

profile = httpx.get(
    f"{base_url}/tenants/tenant_designtechco/brands/brand_nova/profiles/profile_nova_v3",
    headers=auth,
    timeout=2.0,
)
profile.raise_for_status()
profile_payload = profile.json()
assert profile_payload["requestId"] == "req_profile_001"
assert profile_payload["profileVersionId"] == "profile_nova_v3"
assert profile_payload["confidence"] == "high"
assert "visualNotes" in profile_payload["profile"]

approval = httpx.post(
    f"{base_url}/tenants/tenant_designtechco/brands/brand_nova/profiles/profile_nova_v3/approve",
    headers=auth,
    json={"approved": True, "makeActive": True, "reviewComment": "Approved for pilot copy and placeholder generation."},
    timeout=2.0,
)
approval.raise_for_status()
assert approval.json()["status"] == "active"
print("[verify-api] PDF/admin/governance PASS")
PY

echo "[verify-api] step 4: model-backed operations, image lifecycle, apply event, and reporting"
"$PY" - "$API_URL" <<'PY'
import sys
import httpx

base_url = sys.argv[1]
auth = {"Authorization": "Bearer demo_plugin_session"}
model_headers = auth | {"Idempotency-Key": "verify-api"}

quality = httpx.post(f"{base_url}/quality/model-gateway/evaluate", headers=auth, timeout=2.0)
quality.raise_for_status()
quality_payload = quality.json()
assert quality_payload["qualityRunId"] == "quality_run_001"
assert quality_payload["provider"] == "mock-provider"
assert quality_payload["model"] == "mock-gpt-4o-equivalent"
assert quality_payload["threshold"] == 0.9
assert quality_payload["score"] >= quality_payload["threshold"]
assert quality_payload["passed"] is True
assert quality_payload["sampleCount"] == 3
assert all(result["passed"] for result in quality_payload["results"])
assert quality_payload["qualityGate"]["goldenSampleSet"] == "project/poc/fixtures/golden-samples.json"

copy_payload = {
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
copy_response = httpx.post(f"{base_url}/plugin/copy/generate", headers=model_headers, json=copy_payload, timeout=2.0)
copy_response.raise_for_status()
copy_payload_response = copy_response.json()
assert copy_payload_response["requestId"] == "req_copy_001"
assert copy_payload_response["usageEventId"] == "usage_copy_001"
assert copy_payload_response["status"] == "completed"
assert len(copy_payload_response["results"]) == 2

loc_payload = {
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
loc_response = httpx.post(f"{base_url}/plugin/copy/localize", headers=model_headers, json=loc_payload, timeout=2.0)
loc_response.raise_for_status()
loc_payload_response = loc_response.json()
assert loc_payload_response["requestId"] == "req_loc_001"
assert len(loc_payload_response["results"][0]["localizations"]) == 8

unsupported_locale = httpx.post(
    f"{base_url}/plugin/copy/localize",
    headers=model_headers,
    json={**loc_payload, "locales": ["en-US"]},
    timeout=2.0,
)
assert unsupported_locale.status_code == 400
assert unsupported_locale.json()["error"]["code"] == "unsupported_locale"
assert unsupported_locale.json()["error"]["details"]["unsupportedLocales"] == ["en-US"]

img_payload = {
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
blocked_image = httpx.post(
    f"{base_url}/plugin/images/jobs",
    headers=model_headers,
    json=img_payload | {
        "clientRequestId": "client_img_blocked_001",
        "prompt": "Public figure wearing a protected logo for a final campaign ad",
    },
    timeout=2.0,
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

created = httpx.post(f"{base_url}/plugin/images/jobs", headers=model_headers, json=img_payload, timeout=2.0)
created.raise_for_status()
assert created.json()["requestId"] == "req_img_001"

statuses = [httpx.get(f"{base_url}/plugin/images/jobs/job_img_001", headers=auth, timeout=2.0).json() for _ in range(3)]
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
assert statuses[-1]["asset"]["url"].startswith(base_url.rstrip("/") + "/")

asset = httpx.get(f"{base_url}/assets/asset_img_001.png", timeout=2.0)
asset.raise_for_status()
assert asset.headers["content-type"] == "image/png"
assert asset.content.startswith(b"\x89PNG\r\n\x1a\n")

missing_asset = httpx.get(f"{base_url}/assets/missing_asset.png", timeout=2.0)
assert missing_asset.status_code == 404
assert missing_asset.json()["error"]["code"] == "asset_not_found"

apply_response = httpx.post(
    f"{base_url}/plugin/apply-events",
    headers=auth,
    json={
        "operationId": "op_copy_001",
        "appliedBy": "usr_maya",
        "appliedItems": [{"layerId": "txt_headline", "outputId": "v1", "outputType": "copy"}],
    },
    timeout=2.0,
)
apply_response.raise_for_status()
assert apply_response.json()["requestId"] == "req_apply_001"

report = httpx.get(f"{base_url}/reports/usage", headers=auth, timeout=2.0)
report.raise_for_status()
payload = report.json()
assert payload["requestId"] == "req_usage_001"
assert payload["summary"]["operationCount"] == 3
assert payload["summary"]["appliedCount"] == 1
assert payload["summary"]["copyOperations"] == 1
assert payload["summary"]["localizationOperations"] == 1
assert payload["summary"]["imageJobs"] == 1
assert payload["summary"]["totalOperations"] == 4
assert payload["byUser"][0]["operations"] == 3
assert len(payload["recentAuditEvents"]) >= 4

duplicate_copy = httpx.post(f"{base_url}/plugin/copy/generate", headers=model_headers, json=copy_payload, timeout=2.0)
duplicate_copy.raise_for_status()
duplicate_report = httpx.get(f"{base_url}/reports/usage", headers=auth, timeout=2.0).json()
assert duplicate_report["summary"]["copyOperations"] == 1
assert duplicate_report["summary"]["totalOperations"] == 4
print("[verify-api] model/image/report PASS")
PY

echo "verify-api: PASS"
