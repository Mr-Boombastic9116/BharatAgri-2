@echo off
setlocal enabledelayedexpansion

:: Ensure script runs in its own directory
cd /d "%~dp0"

echo ========================================================
echo       BHARATAGRI ITERATION 2 - LOCAL STARTUP
echo ========================================================
echo Working Directory: %CD%
echo.

:: 1. Check Python
echo [1/8] Checking Python environment...
where python >nul 2>nul
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
    ) else if exist "C:\Python312\python.exe" (
        set "PATH=C:\Python312;C:\Python312\Scripts;%PATH%"
    ) else (
        echo [ERROR] Python 3 is not found in PATH!
        echo Please install Python 3.10+ from https://www.python.org/ and check "Add Python to PATH".
        pause
        exit /b 1
    )
)
python --version
echo [OK] Python is available.
echo.

:: 2. Check Node / npm
echo [2/8] Checking Node.js and npm...
where npm >nul 2>nul
if %errorlevel% neq 0 (
    if exist "%USERPROFILE%\.local\node\npm.cmd" (
        set "PATH=%USERPROFILE%\.local\node;%PATH%"
    ) else if exist "C:\Program Files\nodejs\npm.cmd" (
        set "PATH=C:\Program Files\nodejs;%PATH%"
    ) else (
        echo [ERROR] Node.js and npm are not found in PATH!
        echo Please install Node.js 18+ from https://nodejs.org/ or add it to PATH.
        pause
        exit /b 1
    )
)
call node --version
call npm --version
echo [OK] Node and npm are available.
echo.

:: 3. Check MySQL / XAMPP Availability
echo [3/8] Checking MySQL connection on port 3306...
netstat -ano | findstr :3306 >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] MySQL service does not appear to be active on port 3306!
    echo If you are using XAMPP, please open the XAMPP Control Panel and start MySQL.
    echo If MySQL is starting or you have external DB, press any key to continue.
    pause
) else (
    echo [OK] MySQL service detected on port 3306.
)
echo.

:: 4. Check .env configuration
echo [4/8] Checking configuration (.env)...
if not exist ".env" (
    if exist ".env.example" (
        echo [.env missing] Copying .env.example to .env ...
        copy .env.example .env
        echo [OK] Created .env with default XAMPP settings.
    ) else (
        echo [ERROR] Neither .env nor .env.example found!
        pause
        exit /b 1
    )
) else (
    echo [OK] .env configuration file found.
)
echo.

:: 5. Check Python dependencies
echo [5/8] Checking Python dependencies...
python -c "import fastapi, sqlalchemy, pymysql, xgboost, ortools" >nul 2>nul
if %errorlevel% neq 0 (
    echo [NOTICE] Installing/verifying requirements from requirements.txt...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Python dependencies. Please inspect the output above.
        pause
        exit /b 1
    )
) else (
    echo [OK] Core Python AI, optimization, and backend libraries verified.
)
echo.

:: 6. Start Backend API Server
echo [6/8] Starting FastAPI Backend on http://localhost:5000 ...
start "BharatAgri-Backend" "%~dp0scripts\run-backend.bat"
ping -n 4 127.0.0.1 >nul
echo [OK] Backend server launched.
echo.

:: 7. Start Frontend Vite Server
echo [7/8] Starting Vite Frontend on http://localhost:3000 ...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo [NOTICE] node_modules not found. Installing frontend dependencies...
    call npm install
)
cd /d "%~dp0"
start "BharatAgri-Frontend" "%~dp0scripts\run-frontend.bat"
ping -n 4 127.0.0.1 >nul
echo [OK] Frontend development server launched.
echo.

:: 8. Launch Browser
echo [8/8] Opening BharatAgri Portal in browser...
start http://localhost:3000

echo.
echo ========================================================
echo   BharatAgri Iteration 2 is now running!
echo   Frontend : http://localhost:3000
echo   Backend  : http://localhost:5000
echo   API Docs : http://localhost:5000/docs
echo   Health   : http://localhost:5000/api/health
echo ========================================================
echo.
echo Backend and Frontend are running in their own separate console windows.
echo You can keep this launcher window open or close it at any time.
echo.
pause
