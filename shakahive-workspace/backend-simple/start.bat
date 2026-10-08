@echo off
echo Starting NOVARAai Backend with Real AI...
echo.

REM Install dependencies if not already installed
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start the server
echo.
echo Starting server on http://localhost:8000
python main.py
