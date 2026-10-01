@echo off
setlocal enabledelayedexpansion

:: Ensure script runs in its own directory
cd /d "%~dp0"

echo ========================================================
echo       BHARATAGRI ITERATION 2 - AUTOMATIC SETUP & LAUNCH
echo ========================================================
echo Working Directory: %CD%
echo.

:: 1. Detect Python
echo [1/8] Detecting Python installation...
set "PYTHON_CMD="
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
    set "PYTHON_CMD=python"
) else if exist "C:\Python312\python.exe" (
    set "PATH=C:\Python312;C:\Python312\Scripts;%PATH%"
    set "PYTHON_CMD=python"
) else if exist "C:\Program Files\Python312\python.exe" (
    set "PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%PATH%"
    set "PYTHON_CMD=python"
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python 3 is not found on this system.
    echo Please install Python 3.10+ from https://www.python.org/ and check "Add Python to PATH".
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('%PYTHON_CMD% --version 2^>^&1') do echo [OK] Found: %%v
echo.

:: 2. Detect Node.js / npm
echo [2/8] Detecting Node.js and npm...
set "NPM_CMD="
where npm >nul 2>nul
if %errorlevel% equ 0 (
    set "NPM_CMD=npm"
) else if exist "%USERPROFILE%\.local\node\npm.cmd" (
    set "PATH=%USERPROFILE%\.local\node;%PATH%"
    set "NPM_CMD=npm"
) else if exist "C:\Program Files\nodejs\npm.cmd" (
    set "PATH=C:\Program Files\nodejs;%PATH%"
    set "NPM_CMD=npm"
)

if "%NPM_CMD%"=="" (
    echo [ERROR] Node.js and npm are not found in PATH or standard locations.
    echo Please install Node.js 18+ from https://nodejs.org/ to run the frontend.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('call node --version 2^>^&1') do echo [OK] Found Node: %%v
for /f "tokens=*" %%v in ('call npm --version 2^>^&1') do echo [OK] Found npm: %%v
echo.

:: 3. Python Virtual Environment Detection / Setup
echo [3/8] Checking Python Virtual Environment...
set "VENV_PYTHON="
set "VENV_PIP="
if exist "venv\Scripts\python.exe" (
    set "VENV_PYTHON=%CD%\venv\Scripts\python.exe"
    set "VENV_PIP=%CD%\venv\Scripts\pip.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"
    set "VENV_PIP=%CD%\.venv\Scripts\pip.exe"
) else (
    echo [Virtual environment missing] Creating Python virtual environment in venv ...
    %PYTHON_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo [WARNING] Failed to create virtual environment. Falling back to system Python.
        set "VENV_PYTHON=%PYTHON_CMD%"
        set "VENV_PIP=%PYTHON_CMD% -m pip"
    ) else (
        echo [OK] Virtual environment created.
        set "VENV_PYTHON=%CD%\venv\Scripts\python.exe"
        set "VENV_PIP=%CD%\venv\Scripts\pip.exe"
    )
)
echo [OK] Using Python: %VENV_PYTHON%
echo.

:: 4. Install Missing Python Dependencies
echo [4/8] Verifying Python dependencies...
"%VENV_PYTHON%" -c "import fastapi, uvicorn, sqlalchemy, pymysql, xgboost, ortools" >nul 2>nul
if %errorlevel% neq 0 (
    echo [NOTICE] Installing missing Python requirements from requirements.txt...
    "%VENV_PIP%" install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Python dependencies. Please verify your internet connection or C++ runtime.
        pause
        exit /b 1
    )
    echo [OK] Python dependencies installed successfully.
) else (
    echo [OK] All core Python packages are already installed.
)
echo.

:: 5. Install Missing Frontend Dependencies
echo [5/8] Verifying Node frontend dependencies...
cd /d "%~dp0frontend"
if not exist "node_modules\vite" (
    echo [NOTICE] Installing frontend dependencies using npm install...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install frontend dependencies.
        pause
        exit /b 1
    )
    echo [OK] Frontend packages installed successfully.
) else (
    echo [OK] Frontend node_modules verified.
)
cd /d "%~dp0"
echo.

:: 6. Check MySQL and Database Existence
echo [6/8] Checking MySQL connection and BharatAgri database...
netstat -ano | findstr :3306 >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] MySQL service does not appear to be active on port 3306!
    echo If using XAMPP, please start Apache and MySQL from the XAMPP Control Panel.
    echo If MySQL is starting or you have an external DB running, press any key to continue.
    pause
) else (
    echo [OK] MySQL port 3306 detected active.
)

:: Verify or safe auto-initialize database
"%VENV_PYTHON%" -c "import pymysql; conn = pymysql.connect(host='localhost', user='root', password='', port=3306); cur = conn.cursor(); cur.execute('SHOW DATABASES LIKE \"bharatagri_iteration2\"'); db = cur.fetchone(); exit(0 if db else 1)" >nul 2>nul
if %errorlevel% neq 0 (
    echo [NOTICE] Database 'bharatagri_iteration2' does not exist yet.
    echo [NOTICE] Initializing database safely from database/bharatagri_iteration2.sql ...
    "%VENV_PYTHON%" -c "import pymysql; conn = pymysql.connect(host='localhost', user='root', password='', port=3306); cur = conn.cursor(); cur.execute('CREATE DATABASE IF NOT EXISTS bharatagri_iteration2 CHARACTER SET utf8mb4'); print('Created database bharatagri_iteration2')"
    where mysql >nul 2>nul
    if %errorlevel% equ 0 (
        mysql -u root bharatagri_iteration2 < database\bharatagri_iteration2.sql
        echo [OK] Initialized schema and dataset from database/bharatagri_iteration2.sql.
    ) else if exist "C:\xampp\mysql\bin\mysql.exe" (
        "C:\xampp\mysql\bin\mysql.exe" -u root bharatagri_iteration2 < database\bharatagri_iteration2.sql
        echo [OK] Initialized schema and dataset using XAMPP mysql binary.
    ) else (
        echo [INFO] Please import database/bharatagri_iteration2.sql into your MySQL server if tables are empty.
    )
) else (
    echo [OK] Database 'bharatagri_iteration2' exists. Preserving existing data safely.
)
echo.

:: 7. Launch Backend API Server
echo [7/8] Starting FastAPI Backend on http://localhost:5000 ...
start "BharatAgri-Backend" cmd /k "cd /d "%CD%" && set PYTHONPATH=. && "%VENV_PYTHON%" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 5000 --reload"
ping -n 4 127.0.0.1 >nul
echo [OK] Backend server process launched.
echo.

:: 8. Launch Frontend & Browser
echo [8/8] Starting Vite Frontend on http://localhost:3000 ...
start "BharatAgri-Frontend" cmd /k "cd /d "%CD%\frontend" && call npm run dev"
ping -n 4 127.0.0.1 >nul
echo [OK] Frontend development server launched.
echo.

echo Opening BharatAgri Portal in browser...
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
echo Backend and Frontend are running in separate console windows.
pause
