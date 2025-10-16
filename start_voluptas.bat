@echo off
cd /d "C:\ITS_QA\VoluptAS"
call .venv\Scripts\activate.bat
echo Starting VoluptAS GUI...
python main.py
pause
