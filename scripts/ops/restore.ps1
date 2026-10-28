# LegalJarvis Database Restore Script (PowerShell)
param (
    [string]$File = ""
)
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($File -ne "") {
    python "$scriptDir\db_backup_restore.py" restore --file $File
} else {
    python "$scriptDir\db_backup_restore.py" restore
}
exit $LASTEXITCODE
