#!/usr/bin/env bash
# run_dev.sh — Start Clearpath backend + frontend dev servers.
#
# Usage: bash scripts/run_dev.sh
#
# Starts:
#   - Backend: uvicorn on port 8000 (with --reload)
#   - Frontend: vite dev server on port 5173
#
# Both processes are killed together on Ctrl+C (trap EXIT).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKEND_DIR="$PROJECT_ROOT"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VENV_DIR="$PROJECT_ROOT/venv"

echo "========================================"
echo " Clearpath Dev Server"
echo "========================================"
echo "  Project root : $PROJECT_ROOT"
echo "  Backend port : 8000"
echo "  Frontend port: 5173"
echo "========================================"
echo ""

# ---- Activate Python venv if present ----------------------------------
if [ -f "$VENV_DIR/bin/activate" ]; then
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
    echo "[backend] Activated venv: $VENV_DIR"
fi

# ---- Check for node_modules -------------------------------------------
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "[frontend] node_modules missing — running npm install..."
    (cd "$FRONTEND_DIR" && npm install)
fi

# ---- PID bookkeeping --------------------------------------------------
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "[dev] Shutting down servers..."
    [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
    echo "[dev] Done."
}

trap cleanup EXIT INT TERM

# ---- Start backend ----------------------------------------------------
echo "[backend] Starting uvicorn on http://localhost:8000 ..."
(cd "$BACKEND_DIR" && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload 2>&1 | sed 's/^/[backend] /') &
BACKEND_PID=$!

# ---- Start frontend ---------------------------------------------------
echo "[frontend] Starting Vite dev server on http://localhost:5173 ..."
(cd "$FRONTEND_DIR" && npm run dev 2>&1 | sed 's/^/[frontend] /') &
FRONTEND_PID=$!

echo ""
echo "[dev] Both servers started. Press Ctrl+C to stop."
echo ""

# ---- Wait for either process to exit ----------------------------------
wait -n "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
