$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location "$projectRoot/frontend"
try {
    python -m http.server 8001
} finally {
    Pop-Location
}
