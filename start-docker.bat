@echo off
setlocal

echo Building and starting the application container...
docker compose up --build

if errorlevel 1 (
    echo.
    echo Docker Compose failed to start the application.
    pause
)
