@echo off
setlocal ENABLEEXTENSIONS
REM Change to the directory of this script
cd /d "%~dp0"

REM Ensure environment is ready
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\bootstrap.ps1"

REM Activate venv
call .venv\Scripts\activate.bat

REM Run app
set PYTHONUTF8=1
echo Starting VoluptAS GUI...
python main.py

endlocal
