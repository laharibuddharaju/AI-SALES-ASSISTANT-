# =====================================================================
# AI Sales Assistant — Backend Startup Script
# =====================================================================
# Usage: Right-click → Run with PowerShell
#        OR from terminal: .\start.ps1
# =====================================================================

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  AI Sales Assistant Backend v2.0     " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check venv
if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "[ERROR] Virtual environment not found." -ForegroundColor Red
    Write-Host "  Run: python -m venv venv && .\venv\Scripts\pip.exe install -r requirements.txt"
    exit 1
}

# Check .env
if (-not (Test-Path ".\.env")) {
    Write-Host "[WARN] .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".\.env.example" ".\.env"
    Write-Host "[WARN] Please edit .env and set your SECRET_KEY before continuing." -ForegroundColor Yellow
}

# Find an available port (try 8000 first, fall back to 8001)
$Port = 8000
$used = netstat -ano | Select-String ":$Port .*LISTEN"
if ($used) {
    Write-Host "[INFO] Port $Port is in use, switching to 8001" -ForegroundColor Yellow
    $Port = 8001
}

Write-Host "[INFO] Starting server on http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "[INFO] API docs: http://127.0.0.1:$Port/docs" -ForegroundColor Green
Write-Host "[INFO] Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

# Apply migrations
Write-Host "[INFO] Running database migrations..." -ForegroundColor Cyan
.\venv\Scripts\python.exe -m alembic upgrade head 2>&1 | Select-String "Running|INFO" | ForEach-Object { Write-Host "  " $_ }

Write-Host ""

# Start uvicorn
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload
