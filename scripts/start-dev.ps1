param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [switch]$OpenBrowser
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [Console]::OutputEncoding

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root "venv\Scripts\python.exe"
$stateFile = Join-Path $PSScriptRoot "dev-processes.json"
$runtimeDir = Join-Path $root "backend\data\runtime"
$backendOut = Join-Path $runtimeDir "backend.out.log"
$backendErr = Join-Path $runtimeDir "backend.err.log"
$frontendOut = Join-Path $runtimeDir "frontend.out.log"
$frontendErr = Join-Path $runtimeDir "frontend.err.log"

function Assert-PortFree {
    param(
        [int]$Port,
        [string]$Name
    )

    $occupied = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($occupied) {
        throw "$Name port $Port is already in use. Free the port and try again."
    }
}

if (-not (Test-Path $python)) {
    throw "Python executable not found: $python"
}

if (Test-Path $stateFile) {
    throw "Existing dev state found at $stateFile. Run .\stop.ps1 before starting again."
}

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
Assert-PortFree -Port $BackendPort -Name "Backend"
Assert-PortFree -Port $FrontendPort -Name "Frontend"

$backendArgs = @(
    "-m", "uvicorn",
    "backend.app.main:app",
    "--host", "127.0.0.1",
    "--port", "$BackendPort",
    "--reload"
)

$frontendArgs = @(
    "-m", "http.server",
    "$FrontendPort",
    "--bind", "127.0.0.1"
)

$backend = Start-Process -FilePath $python -ArgumentList $backendArgs -WorkingDirectory $root -PassThru -WindowStyle Hidden -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr
$frontend = Start-Process -FilePath $python -ArgumentList $frontendArgs -WorkingDirectory $root -PassThru -WindowStyle Hidden -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr

$payload = @{
    backend_pid = $backend.Id
    frontend_pid = $frontend.Id
    backend_url = "http://127.0.0.1:$BackendPort"
    frontend_url = "http://127.0.0.1:$FrontendPort"
    started_at = (Get-Date).ToString("s")
} | ConvertTo-Json

$payload | Set-Content -Path $stateFile -Encoding UTF8

Write-Host ""
Write-Host "AuditPilot dev stack started." -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
Write-Host "Backend:  http://127.0.0.1:$BackendPort"
Write-Host "Swagger:  http://127.0.0.1:$BackendPort/docs"
Write-Host ""
Write-Host "Log files:"
Write-Host "  $backendOut"
Write-Host "  $backendErr"
Write-Host "  $frontendOut"
Write-Host "  $frontendErr"
Write-Host ""
Write-Host "Stop command: .\stop.ps1"

if ($OpenBrowser) {
    Start-Process "http://127.0.0.1:$FrontendPort"
}
