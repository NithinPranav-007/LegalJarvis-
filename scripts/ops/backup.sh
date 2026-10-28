#!/usr/bin/env bash
# LegalJarvis Database Backup Script (Bash)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python}"

"$PYTHON" "$SCRIPT_DIR/db_backup_restore.py" backup
