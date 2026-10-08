@echo off
title BharatAgri-Frontend
cd /d "%~dp0..\frontend"
set "FRONTEND_DIR=%~dp0..\frontend"

:: Check and append Node/npm to PATH if installed in user or program directories
where npm >nul 2>nul
if %errorlevel% neq 0 (
    if exist "%USERPROFILE%\.local\node\npm.cmd" (
        set "PATH=%USERPROFILE%\.local\node;%PATH%"
    ) else if exist "C:\Program Files\nodejs\npm.cmd" (
        set "PATH=C:\Program Files\nodejs;%PATH%"
    ) else if exist "%APPDATA%\npm\npm.cmd" (
        set "PATH=%APPDATA%\npm;%PATH%"
    )
)

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] npm is not found in PATH or standard installation locations.
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules\vite" (
    echo [NOTICE] Frontend node_modules missing. Installing via npm install...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
)

echo ========================================================
echo   BHARATAGRI FRONTEND DEV SERVER (VITE)
echo   Directory:    %CD%
echo   Listening on: http://localhost:3000
echo ========================================================
call npm run dev
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Frontend Vite server stopped with exit code %errorlevel%.
    echo Please inspect the error logs above.
)
pause
