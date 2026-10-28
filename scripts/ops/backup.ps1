# LegalJarvis Database Backup Script (PowerShell)
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$scriptDir\db_backup_restore.py" backup
exit $LASTEXITCODE
