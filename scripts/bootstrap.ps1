param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

# Move to repo root (script directory)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir\..

Write-Host "== VoluptAS Bootstrap =="
Write-Host "Repo: $(Get-Location)"

# Ensure Python
$pythonCmds = @('py -3.11','py -3','python')
$python = $null
foreach ($cmd in $pythonCmds) {
  try { & $cmd --version > $null 2>&1; $python = $cmd; break } catch {}
}
if (-not $python) { throw 'Python not found. Install Python 3.11+ and rerun.' }
Write-Host "Using Python via: $python"

# Create venv if missing
$venvPython = Join-Path (Get-Location) ".venv/Scripts/python.exe"
if (-not (Test-Path $venvPython) -or $Force) {
  Write-Host "Creating virtual environment (.venv)..."
  & $python -m venv .venv
}

# Activate venv
$activate = ".venv/Scripts/Activate.ps1"
. $activate

# Upgrade pip and install
python -m pip install -U pip setuptools wheel
if (Test-Path "requirements.txt") {
  Write-Host "Installing dependencies from requirements.txt..."
  pip install -r requirements.txt
} else {
  Write-Host "requirements.txt not found; installing minimal deps..."
  pip install PyQt6 SQLAlchemy networkx matplotlib requests python-dotenv gspread google-auth numpy
}

Write-Host "Bootstrap complete."
