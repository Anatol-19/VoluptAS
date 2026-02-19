@echo off
chcp 65001 >nul
setlocal ENABLEEXTENSIONS
REM ====================================
REM VoluptAS - Setup Script
REM ====================================

cd /d "%~dp0"

echo.
echo ====================================
echo   VoluptAS Setup
echo ====================================
echo Working directory: %CD%
echo.

REM Check Python
echo [1/4] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.11+ and add to PATH
    pause
    exit /b 1
)

python --version
echo.

REM Create venv if missing
echo [2/4] Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists
)
echo.

REM Activate venv
echo [3/4] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Install/Update dependencies
echo [4/4] Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo ====================================
echo   Setup Complete!
echo ====================================
echo.
echo To run VoluptAS: start_voluptas.bat
echo.

endlocal
