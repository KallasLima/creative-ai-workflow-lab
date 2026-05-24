#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
POC="$ROOT/project/poc"
BACKEND="$POC/backend"
FRONTEND="$POC/frontend"
VENV="$BACKEND/.venv"
PY="$VENV/bin/python"
PYTHON_BIN="${PYTHON_BIN:-}"
API_URL="http://127.0.0.1:8000"
FRONTEND_URL="http://127.0.0.1:5173"
TMP_DIR=""
DB_PATH=""
BACKEND_LOG=""
FRONTEND_LOG=""
BACKEND_PID=""
FRONTEND_PID=""
SMOKE_MODE="0"
LOCK_DIR="$POC/.run-lock"
LOCK_ACQUIRED="0"

if [ "${1:-}" = "--smoke" ]; then
  SMOKE_MODE="1"
elif [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  cat <<'EOF'
Usage: project/poc/scripts/run-demo.sh [--smoke]

Starts the local backend and browser fallback harness in real-backend mode.

Options:
  --smoke   Start both services, wait until they are ready, then stop and clean up.
EOF
  exit 0
elif [ -n "${1:-}" ]; then
  echo "[run-demo] unknown argument: $1" >&2
  echo "[run-demo] run with --help for usage" >&2
  exit 1
fi

find_python() {
  if [ -n "$PYTHON_BIN" ]; then
    if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
      command -v "$PYTHON_BIN"
      return
    fi
    echo "[run-demo] PYTHON_BIN is set but was not found: $PYTHON_BIN" >&2
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
  echo "[run-demo] python3 or python is required" >&2
  exit 1
}

acquire_lock() {
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    write_lock
    return
  fi

  if lock_is_active; then
    echo "[run-demo] another POC script is already running; wait for it to finish before starting the demo" >&2
    exit 1
  fi

  echo "[run-demo] removing stale POC run lock" >&2
  rm -rf "$LOCK_DIR"
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    write_lock
    return
  fi

  echo "[run-demo] another POC script is already running; wait for it to finish before starting the demo" >&2
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

wait_for_http() {
  local url="${1:-}"
  local label="${2:-service}"
  local log_file="${3:-}"

  "$PY" - "$url" "$label" "$log_file" <<'PY'
import sys
import time

import httpx

url = sys.argv[1]
label = sys.argv[2]
log_file = sys.argv[3]
for _ in range(60):
    try:
        response = httpx.get(url, timeout=1.0)
        if response.status_code == 200:
            raise SystemExit(0)
    except Exception:
        pass
    time.sleep(0.25)
print(f"[run-demo] {label} failed to become ready: {url}")
if log_file:
    print(f"[run-demo] check log: {log_file}")
raise SystemExit(1)
PY
}

cleanup() {
  local status="${1:-$?}"
  trap - EXIT INT TERM

  kill_tree "$FRONTEND_PID"
  kill_tree "$BACKEND_PID"

  if [ -n "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
  fi
  rm -rf "$VENV" "$FRONTEND/node_modules" "$FRONTEND/dist"
  find "$BACKEND" "$FRONTEND" \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} + 2>/dev/null || true
  if [ "$LOCK_ACQUIRED" = "1" ]; then
    rm -rf "$LOCK_DIR"
  fi
  echo "[run-demo] cleaned generated artifacts and stopped child processes"
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
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/creative-ai-workflow-demo.XXXXXX")"
DB_PATH="$TMP_DIR/demo.sqlite"
BACKEND_LOG="$TMP_DIR/backend.log"
FRONTEND_LOG="$TMP_DIR/frontend.log"

if ! port_is_free 8000; then
  echo "[run-demo] port 8000 is already in use; stop the existing listener before running the demo"
  exit 1
fi

if ! port_is_free 5173; then
  echo "[run-demo] port 5173 is already in use; stop the existing listener before running the demo"
  exit 1
fi

if [ ! -x "$PY" ]; then
  "$PYTHON_BIN" -m venv "$VENV"
fi

"$PY" -m pip install -q -r "$BACKEND/requirements.txt"

if ! command -v npm >/dev/null 2>&1; then
  echo "[run-demo] npm is required for the frontend demo" >&2
  exit 1
fi

if [ ! -d "$FRONTEND/node_modules" ]; then
  npm --prefix "$FRONTEND" ci
fi

echo "[run-demo] starting backend at $API_URL"
(cd "$BACKEND" && POC_DB_PATH="$DB_PATH" "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > "$BACKEND_LOG" 2>&1) &
BACKEND_PID="$!"

wait_for_http "$API_URL/health" "backend" "$BACKEND_LOG"

cat <<EOF
[run-demo] backend ready: $API_URL
[run-demo] browser fallback harness target: $FRONTEND_URL
[run-demo] demo guide: project/poc/demo/README.md
[run-demo] stop backend and browser fallback harness with Ctrl-C
EOF

if [ "$SMOKE_MODE" = "1" ]; then
  (cd "$FRONTEND" && VITE_API_BASE_URL="$API_URL" npm run dev > "$FRONTEND_LOG" 2>&1) &
else
  (cd "$FRONTEND" && VITE_API_BASE_URL="$API_URL" npm run dev) &
fi
FRONTEND_PID="$!"

wait_for_http "$FRONTEND_URL" "frontend" "$FRONTEND_LOG"
echo "[run-demo] frontend ready: $FRONTEND_URL"

if [ "$SMOKE_MODE" = "1" ]; then
  echo "[run-demo] smoke mode complete; stopping demo"
  exit 0
fi

wait "$FRONTEND_PID"
