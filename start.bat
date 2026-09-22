@echo off

if not exist .venv (
    echo ERROR: Virtual environment not found.
    echo Run the setup script first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Preparing frontend...
call scripts\build_frontend.bat

echo Starting application...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
