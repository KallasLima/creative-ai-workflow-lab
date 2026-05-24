#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
POC="$ROOT/project/poc"
BACKEND="$POC/backend"
FRONTEND="$POC/frontend"
VENV="$BACKEND/.venv"
PY="$VENV/bin/python"
PYTHON_BIN="${PYTHON_BIN:-}"
RUN_FRONTEND_VERIFY="${RUN_FRONTEND_VERIFY:-1}"
TMP_DIR=""
DB_PATH=""
LOG_FILE=""
API_URL="http://127.0.0.1:8000"
STARTED_PID=""
LOCK_DIR="$POC/.run-lock"
LOCK_ACQUIRED="0"

find_python() {
  if [ -n "$PYTHON_BIN" ]; then
    if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
      command -v "$PYTHON_BIN"
      return
    fi
    echo "[verify-all] PYTHON_BIN is set but was not found: $PYTHON_BIN" >&2
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
  echo "[verify-all] python3 or python is required" >&2
  exit 1
}

acquire_lock() {
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    write_lock
    return
  fi

  if lock_is_active; then
    echo "[verify-all] another POC script is already running; wait for it to finish before running verification" >&2
    exit 1
  fi

  echo "[verify-all] removing stale POC run lock" >&2
  rm -rf "$LOCK_DIR"
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    write_lock
    return
  fi

  echo "[verify-all] another POC script is already running; wait for it to finish before running verification" >&2
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
  local status="${1:-$?}"
  trap - EXIT INT TERM

  kill_tree "$STARTED_PID"

  if [ -n "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
  fi
  rm -rf "$VENV" "$FRONTEND/node_modules" "$FRONTEND/dist"
  find "$BACKEND" "$FRONTEND" \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} + 2>/dev/null || true
  if [ "$LOCK_ACQUIRED" = "1" ]; then
    rm -rf "$LOCK_DIR"
  fi
  echo "[verify-all] cleaned generated artifacts and stopped child processes"
  exit "$status"
}

kill_tree() {
  local pid="${1:-}"
  local child

  if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
    return
  fi

  for child in $(pgrep -P "$pid" 2>/dev/null || true); do
    kill_tree "$child"
  done

  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}

trap 'cleanup 130' INT
trap 'cleanup 143' TERM
trap 'cleanup $?' EXIT

acquire_lock
PYTHON_BIN="$(find_python)"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/creative-ai-workflow-verify-all.XXXXXX")"
DB_PATH="$TMP_DIR/verify-all.sqlite"
LOG_FILE="$TMP_DIR/verify-all.log"

if ! port_is_free 8000; then
  echo "[verify-all] port 8000 is already in use; stop the existing listener before running verification"
  exit 1
fi

if [ ! -x "$PY" ]; then
  "$PYTHON_BIN" -m venv "$VENV"
fi

"$PY" -m pip install -q -r "$BACKEND/requirements.txt"

echo "[verify-all] backend pytest"
(cd "$BACKEND" && "$PY" -m pytest)

echo "[verify-all] starting backend for end-to-end checks"
(cd "$BACKEND" && POC_DB_PATH="$DB_PATH" "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > "$LOG_FILE" 2>&1) &
STARTED_PID="$!"

"$PY" - "$API_URL" "$LOG_FILE" <<'PY'
import sys
import time

import httpx

base_url = sys.argv[1]
log_file = sys.argv[2]
for _ in range(60):
    try:
        response = httpx.get(f"{base_url}/health", timeout=1.0)
        if response.status_code == 200:
            break
    except Exception:
        pass
    time.sleep(0.25)
else:
    print(f"[verify-all] backend failed to start; log at {log_file}")
    raise SystemExit(1)
print("[verify-all] backend ready")
PY

echo "[verify-all] api verifier"
POC_LOCK_HELD=1 API_URL="$API_URL" "$POC/scripts/verify-api.sh"

if [ -d "$FRONTEND" ]; then
  if [ "$RUN_FRONTEND_VERIFY" != "1" ]; then
    echo "[verify-all] frontend verification disabled by RUN_FRONTEND_VERIFY=0"
  else
    if ! command -v npm >/dev/null 2>&1; then
      echo "[verify-all] npm is required for frontend verification"
      exit 1
    fi
    echo "[verify-all] frontend install"
    npm --prefix "$FRONTEND" install
    echo "[verify-all] frontend smoke"
    npm --prefix "$FRONTEND" run smoke
    echo "[verify-all] frontend build"
    npm --prefix "$FRONTEND" run build
    echo "[verify-all] real-backend smoke via frontend contract"
    POC_LOCK_HELD=1 VITE_API_BASE_URL="$API_URL" "$POC/scripts/verify-real-backend-smoke.sh"
    echo "[verify-all] frontend visual smoke"
    VITE_API_BASE_URL="$API_URL" npm --prefix "$FRONTEND" run visual-smoke
  fi
fi

echo "verify-all: PASS"
