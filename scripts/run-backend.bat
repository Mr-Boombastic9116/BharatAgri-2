@echo off
title BharatAgri-Backend
cd /d "%~dp0.."
set "PROJECT_ROOT=%~dp0.."
set "PYTHONPATH=%PROJECT_ROOT%"

set "PY_EXE="
if exist "%PROJECT_ROOT%\venv\Scripts\python.exe" (
    set "PY_EXE=%PROJECT_ROOT%\venv\Scripts\python.exe"
) else if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    set "PY_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PY_EXE=python"
    ) else (
        where py >nul 2>nul
        if %errorlevel% equ 0 set "PY_EXE=py -3"
    )
)

if "%PY_EXE%"=="" (
    echo [ERROR] Python environment not found. Please run start.bat first.
    pause
    exit /b 1
)

echo ========================================================
echo   BHARATAGRI BACKEND API SERVER (FASTAPI)
echo   Directory:    %CD%
echo   Python:       %PY_EXE%
echo   Listening on: http://localhost:5000
echo   API Docs:     http://localhost:5000/docs
echo   Health:       http://localhost:5000/api/health
echo ========================================================
"%PY_EXE%" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 5000 --reload
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Backend API server stopped with exit code %errorlevel%.
    echo Please inspect the error traceback above.
)
pause
