@echo off
title BharatAgri-Backend
cd /d "%~dp0.."
set PYTHONPATH=.
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
)
echo ========================================================
echo   BHARATAGRI BACKEND API SERVER (FASTAPI)
echo   Listening on: http://localhost:5000
echo   API Docs:     http://localhost:5000/docs
echo ========================================================
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 5000 --reload
pause
