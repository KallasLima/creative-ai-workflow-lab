#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
POC="$ROOT/project/poc"
BACKEND="$POC/backend"
VENV="$BACKEND/.venv"
PY="$VENV/bin/python"
PYTHON_BIN="${PYTHON_BIN:-}"
API_URL="${API_URL:-http://127.0.0.1:8000}"

find_python() {
  if [ -n "$PYTHON_BIN" ]; then
    if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
      command -v "$PYTHON_BIN"
      return
    fi
    echo "[benchmark-latency] PYTHON_BIN is set but was not found: $PYTHON_BIN" >&2
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
  echo "[benchmark-latency] python3 or python is required" >&2
  exit 1
}

PYTHON_BIN="$(find_python)"

if [ ! -x "$PY" ]; then
  "$PYTHON_BIN" -m venv "$VENV"
  "$PY" -m pip install -q -r "$BACKEND/requirements.txt"
fi

"$PY" - "$API_URL" <<'PY'
import statistics
import sys
import time

import httpx

base_url = sys.argv[1].rstrip("/")
auth = {"Authorization": "Bearer demo_plugin_session"}

copy_payload = {
    "clientRequestId": "benchmark_copy_001",
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

loc_payload = {
    "clientRequestId": "benchmark_loc_001",
    "contractVersion": "2026-05-poc",
    "pluginVersion": "0.1.0",
    "tenantId": "tenant_designtechco",
    "brandId": "brand_nova",
    "profileId": "profile_nova_v3",
    "channel": "mobile",
    "locales": ["fr-FR", "de-DE", "es-ES", "pt-BR", "it-IT", "nl-NL", "ja-JP", "ko-KR"],
    "layers": [{"layerId": "txt_cta", "text": "Shop the drop"}],
}

img_payload = {
    "clientRequestId": "benchmark_img_001",
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


def request_ms(label, method, path, **kwargs):
    start = time.perf_counter()
    response = httpx.request(method, f"{base_url}{path}", timeout=2.0, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.raise_for_status()
    return elapsed_ms


try:
    httpx.get(f"{base_url}/health", timeout=2.0).raise_for_status()
except Exception as exc:
    raise SystemExit(f"[benchmark-latency] backend is not reachable at {base_url}: {exc}") from exc

checks = {
    "copy_generate": ("POST", "/plugin/copy/generate", copy_payload),
    "copy_localize": ("POST", "/plugin/copy/localize", loc_payload),
    "image_job_create": ("POST", "/plugin/images/jobs", img_payload),
}

for name, (method, path, payload) in checks.items():
    samples = []
    for index in range(5):
        headers = auth | {"Idempotency-Key": f"benchmark-{name}-{index}"}
        sample_payload = dict(payload)
        sample_payload["clientRequestId"] = f"{payload['clientRequestId']}_{index}"
        samples.append(request_ms(name, method, path, headers=headers, json=sample_payload))
    median_ms = statistics.median(samples)
    max_ms = max(samples)
    print(f"[benchmark-latency] {name}: median={median_ms:.1f}ms max={max_ms:.1f}ms")
    if median_ms >= 2000:
        raise SystemExit(f"[benchmark-latency] {name} median exceeded 2000ms")

print("[benchmark-latency] PASS")
PY
