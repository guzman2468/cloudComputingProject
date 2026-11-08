@echo off
setlocal

where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py -3.11"
) else (
    set "PY_CMD=python"
)

if not exist .venv (
    echo Creating virtual environment...
    %PY_CMD% -m venv .venv 2>nul || python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
python -m pip install -r requirements.txt

echo Setup complete.
