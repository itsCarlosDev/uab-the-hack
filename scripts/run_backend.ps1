$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location "$projectRoot/backend"
try {
    uvicorn main:app --reload
} finally {
    Pop-Location
}
