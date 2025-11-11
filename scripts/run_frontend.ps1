$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location "$projectRoot/apps/frontend"
try {
    python -m http.server 8001
} finally {
    Pop-Location
}
