@echo off
chcp 65001 >nul
setlocal ENABLEEXTENSIONS
cd /d "%~dp0"

echo.
echo ====================================
echo VoluptAS Launcher
echo ====================================
echo.

REM Check if venv exists, if not - run setup
if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Running initial setup...
    echo.
    call setup.bat
    exit /b %ERRORLEVEL%
)

REM Activate venv
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    echo Try running setup.bat to recreate it
    pause
    exit /b 1
)

REM Проверка портабельности
python scripts/check_portability.py
if errorlevel 1 (
    echo [ERROR] Portability check failed. Исправьте проблемы перед запуском.
    pause
    exit /b 1
)

REM Run app
echo.
echo Starting VoluptAS...
echo.
set PYTHONUTF8=1
python main.py

endlocal
