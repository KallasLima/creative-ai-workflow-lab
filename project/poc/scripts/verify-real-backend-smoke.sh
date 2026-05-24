#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
POC="$ROOT/project/poc"
BACKEND="$POC/backend"
VENV="$BACKEND/.venv"
PY="$VENV/bin/python"
PYTHON_BIN="${PYTHON_BIN:-}"
API_URL="${VITE_API_BASE_URL:-http://127.0.0.1:8000}"
LOCK_DIR="$POC/.run-lock"
LOCK_ACQUIRED="0"

find_python() {
  if [ -n "$PYTHON_BIN" ]; then
    if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
      command -v "$PYTHON_BIN"
      return
    fi
    echo "[real-backend-smoke] PYTHON_BIN is set but was not found: $PYTHON_BIN" >&2
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
  echo "[real-backend-smoke] python3 or python is required" >&2
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
    echo "[real-backend-smoke] another POC script is already running; wait for it to finish before running the smoke check" >&2
    exit 1
  fi

  echo "[real-backend-smoke] removing stale POC run lock" >&2
  rm -rf "$LOCK_DIR"
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    write_lock
    return
  fi

  echo "[real-backend-smoke] another POC script is already running; wait for it to finish before running the smoke check" >&2
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

cleanup() {
  if [ "$LOCK_ACQUIRED" = "1" ]; then
    rm -rf "$LOCK_DIR"
  fi
}

trap cleanup EXIT
acquire_lock
PYTHON_BIN="$(find_python)"

if [ ! -x "$PY" ]; then
  "$PYTHON_BIN" -m venv "$VENV"
fi

"$PY" -m pip install -q -r "$BACKEND/requirements.txt"

"$PY" - "$API_URL" <<'PY'
import sys

import httpx

base_url = sys.argv[1].rstrip("/")
auth = {"Authorization": "Bearer demo_plugin_session"}

start = httpx.post(f"{base_url}/auth/plugin/start", json={"localNonce": "demo_nonce"}, timeout=2.0)
start.raise_for_status()
assert start.json()["requestId"] == "auth_req_demo"

exchange = httpx.post(
    f"{base_url}/auth/plugin/exchange",
    json={"requestId": "auth_req_demo", "localNonce": "demo_nonce"},
    timeout=2.0,
)
exchange.raise_for_status()
token = exchange.json()["session"]["accessToken"]
assert token == "demo_plugin_session"

headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "frontend-smoke"}

context = httpx.get(f"{base_url}/me/context", headers=auth, timeout=2.0)
context.raise_for_status()
assert context.json()["tenant"]["tenantId"] == "tenant_designtechco"

copy_payload = {
    "clientRequestId": "frontend_copy_001",
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
copy_response = httpx.post(f"{base_url}/plugin/copy/generate", headers=headers, json=copy_payload, timeout=2.0)
copy_response.raise_for_status()
assert copy_response.json()["usageEventId"] == "usage_copy_001"

loc_payload = {
    "clientRequestId": "frontend_loc_001",
    "contractVersion": "2026-05-poc",
    "pluginVersion": "0.1.0",
    "tenantId": "tenant_designtechco",
    "brandId": "brand_nova",
    "profileId": "profile_nova_v3",
    "channel": "mobile",
    "locales": ["fr-FR", "de-DE", "es-ES", "pt-BR", "it-IT", "nl-NL", "ja-JP", "ko-KR"],
    "layers": [{"layerId": "txt_cta", "text": "Shop the drop"}],
}
loc_response = httpx.post(f"{base_url}/plugin/copy/localize", headers=headers, json=loc_payload, timeout=2.0)
loc_response.raise_for_status()
assert len(loc_response.json()["results"][0]["localizations"]) == 8

img_payload = {
    "clientRequestId": "frontend_img_001",
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
created = httpx.post(f"{base_url}/plugin/images/jobs", headers=headers, json=img_payload, timeout=2.0)
created.raise_for_status()
assert created.json()["jobId"] == "job_img_001"

for _ in range(3):
    status = httpx.get(f"{base_url}/plugin/images/jobs/job_img_001", headers=auth, timeout=2.0)
    status.raise_for_status()

asset = httpx.get(f"{base_url}/assets/asset_img_001.png", timeout=2.0)
asset.raise_for_status()
assert asset.headers["content-type"] == "image/png"

print("real-backend-smoke: PASS")
PY
