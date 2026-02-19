@echo off
chcp 65001 >nul
setlocal ENABLEEXTENSIONS
cd /d "%~dp0"

echo.
echo ====================================
echo   VoluptAS Launcher
echo ====================================
echo.

REM Check if venv exists, create if missing
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Make sure Python 3.11+ is installed
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
) else (
    echo [1/3] Virtual environment found
)

REM Activate venv
echo [2/3] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check/install dependencies
echo [3/3] Checking dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo WARNING: Some dependencies failed to install
    echo Continuing anyway...
)

REM Run app
echo.
echo ====================================
echo   Starting VoluptAS...
echo ====================================
echo.
set PYTHONUTF8=1
python main.py

endlocal
