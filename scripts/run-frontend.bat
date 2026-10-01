@echo off
title BharatAgri-Frontend
cd /d "%~dp0..\frontend"

echo ========================================================
echo   BHARATAGRI FRONTEND DEV SERVER (VITE)
echo   Directory:    %CD%
echo   Listening on: http://localhost:3000
echo ========================================================
call npm run dev
pause

