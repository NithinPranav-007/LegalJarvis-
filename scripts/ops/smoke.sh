#!/usr/bin/env bash
# LegalJarvis Deployment Smoke Test (Bash)
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
FRONTEND_URL="${2:-http://localhost:5173}"

echo "================================================="
echo "LegalJarvis Deployment Smoke Test (PRD T-21)"
echo "================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python}"

"$PYTHON" "$SCRIPT_DIR/smoke_harness.py" --base-url "$BASE_URL" --frontend-url "$FRONTEND_URL"
