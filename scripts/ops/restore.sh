#!/usr/bin/env bash
# LegalJarvis Database Restore Script (Bash)
set -euo pipefail

BACKUP_FILE="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python}"

if [ -n "$BACKUP_FILE" ]; then
    "$PYTHON" "$SCRIPT_DIR/db_backup_restore.py" restore --file "$BACKUP_FILE"
else
    "$PYTHON" "$SCRIPT_DIR/db_backup_restore.py" restore
fi
