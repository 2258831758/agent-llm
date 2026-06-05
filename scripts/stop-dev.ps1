$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [Console]::OutputEncoding

$stateFile = Join-Path $PSScriptRoot "dev-processes.json"

if (-not (Test-Path $stateFile)) {
    Write-Host "No running dev state found." -ForegroundColor Yellow
    return
}

$state = Get-Content $stateFile | ConvertFrom-Json
$processIds = @($state.backend_pid, $state.frontend_pid) | Where-Object { $_ }

function Stop-ProcessTree {
    param(
        [int]$ProcessId
    )

    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ProcessId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -ProcessId $child.ProcessId
    }

    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped process $ProcessId"
    }
}

foreach ($processId in $processIds) {
    Stop-ProcessTree -ProcessId $processId
}

Remove-Item $stateFile -Force
Write-Host "AuditPilot dev stack stopped." -ForegroundColor Green
