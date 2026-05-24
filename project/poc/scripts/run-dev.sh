#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

cd "$FRONTEND_DIR"

if ! command -v npm >/dev/null 2>&1; then
  echo "[run-dev] npm is required for the frontend demo" >&2
  exit 1
fi

if [ ! -d node_modules ]; then
  npm ci
fi

if [ -n "${VITE_API_BASE_URL:-}" ]; then
  echo "Starting frontend against VITE_API_BASE_URL=$VITE_API_BASE_URL"
else
  echo "Starting frontend in local mock mode"
fi

npm run dev
