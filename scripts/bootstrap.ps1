# VoluptAS Bootstrap Script
# UTF-8 encoding with BOM

param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Move to repo root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir\..

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "VoluptAS Bootstrap" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Working directory: $(Get-Location)"
Write-Host ""

# Check Python
Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
$pythonCmds = @('python', 'py -3.11', 'py -3', 'py')
$python = $null
foreach ($cmd in $pythonCmds) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $python = $cmd
            Write-Host "Found: $version" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $python) {
    Write-Host "ERROR: Python not found" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
}
Write-Host ""

# Create venv
Write-Host "[2/4] Setting up virtual environment..." -ForegroundColor Yellow
$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython) -or $Force) {
    Write-Host "Creating virtual environment..."
    & $python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Green
}
Write-Host ""

# Activate venv
Write-Host "[3/4] Activating virtual environment..." -ForegroundColor Yellow
$activateScript = ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "ERROR: Activation script not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Install dependencies
Write-Host "[4/4] Installing dependencies..." -ForegroundColor Yellow
python -m pip install --quiet --upgrade pip setuptools wheel

if (Test-Path "requirements.txt") {
    Write-Host "Installing from requirements.txt..."
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "WARNING: requirements.txt not found" -ForegroundColor Yellow
}

# Verify installation
Write-Host "Verifying installation..."
try {
    python -c "import PyQt6; import sqlalchemy; print('Critical packages OK')"
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Some packages may be missing" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Bootstrap Complete!" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Run application: python main.py"
Write-Host "  2. Or use: .\start_voluptas.bat"
Write-Host "  3. DB will auto-initialize on first run"
Write-Host ""
