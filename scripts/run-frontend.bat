@echo off
title BharatAgri-Frontend
cd /d "%~dp0..\frontend"
if exist "%USERPROFILE%\.local\node\npm.cmd" (
    set "PATH=%USERPROFILE%\.local\node;%PATH%"
)
echo ========================================================
echo   BHARATAGRI FRONTEND DEV SERVER (VITE)
echo   Listening on: http://localhost:3000
echo ========================================================
call npm run dev
pause
