@echo off
setlocal enabledelayedexpansion

:: 1. Project path: Must work when extracted anywhere, including folders with spaces
cd /d "%~dp0"
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo ========================================================
echo       BHARATAGRI ITERATION 2 - STARTUP LAUNCHER
echo ========================================================
echo Project Directory: "%PROJECT_ROOT%"
echo.

:: 2. Detect Python (python / py)
echo [1/7] Detecting Python installation...
set "PYTHON_EXE="
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
) else (
    where py >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=py -3"
    )
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python was not found in PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure "Add Python to PATH" is checked during installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('%PYTHON_EXE% --version 2^>^&1') do echo [OK] Found Python: %%v
echo.

:: 3. Python Virtual Environment Detection / Setup & Dependencies
echo [2/7] Checking Python virtual environment and dependencies...
set "VENV_DIR="
set "VENV_PYTHON="

if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    set "VENV_DIR=%PROJECT_ROOT%\.venv"
    set "VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
) else if exist "%PROJECT_ROOT%\venv\Scripts\python.exe" (
    set "VENV_DIR=%PROJECT_ROOT%\venv"
    set "VENV_PYTHON=%PROJECT_ROOT%\venv\Scripts\python.exe"
) else (
    echo [NOTICE] Virtual environment not found. Creating .venv ...
    %PYTHON_EXE% -m venv "%PROJECT_ROOT%\.venv"
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment in .venv.
        pause
        exit /b 1
    )
    set "VENV_DIR=%PROJECT_ROOT%\.venv"
    set "VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
    echo [OK] Virtual environment created at .venv.
)

echo [OK] Using Python environment: "!VENV_PYTHON!"

echo Verifying Python packages from requirements.txt...
"!VENV_PYTHON!" -c "import fastapi, uvicorn, sqlalchemy, pymysql, xgboost, ortools, jose, bcrypt" >nul 2>nul
if !errorlevel! neq 0 (
    echo [NOTICE] Installing missing Python requirements from requirements.txt...
    "%VENV_DIR%\Scripts\pip.exe" install -r "%PROJECT_ROOT%\requirements.txt"
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install Python dependencies. Please check network connection.
        pause
        exit /b 1
    )
    echo [OK] Python dependencies installed successfully.
) else (
    echo [OK] Python dependencies verified.
)
echo.

:: 4. Node.js & npm Detection & Frontend Dependencies
echo [3/7] Detecting Node.js and frontend dependencies...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not found in PATH.
    echo Please install Node.js 18+ from https://nodejs.org/ to run the frontend.
    pause
    exit /b 1
)

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] npm is not found in PATH.
    echo Please install Node.js with npm from https://nodejs.org/
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo [OK] Found Node.js: %%v
for /f "tokens=*" %%v in ('call npm --version 2^>^&1') do echo [OK] Found npm: %%v

if not exist "%PROJECT_ROOT%\frontend\node_modules\vite" (
    echo [NOTICE] Installing frontend packages using npm install...
    cd /d "%PROJECT_ROOT%\frontend"
    call npm install
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install frontend dependencies via npm install.
        cd /d "%PROJECT_ROOT%"
        pause
        exit /b 1
    )
    cd /d "%PROJECT_ROOT%"
    echo [OK] Frontend packages installed successfully.
) else (
    echo [OK] Frontend dependencies verified.
)
echo.

:: 5. Environment Configuration (.env)
echo [4/7] Verifying environment configuration (.env)...
if not exist "%PROJECT_ROOT%\.env" (
    if exist "%PROJECT_ROOT%\.env.example" (
        echo [NOTICE] .env not found. Initializing from .env.example ...
        copy "%PROJECT_ROOT%\.env.example" "%PROJECT_ROOT%\.env" >nul
        echo [OK] Created .env with local development defaults.
    ) else (
        echo [WARNING] .env.example not found. Creating minimal default .env...
        > "%PROJECT_ROOT%\.env" (
            echo DB_HOST=localhost
            echo DB_PORT=3306
            echo DB_USER=root
            echo DB_PASSWORD=
            echo DB_NAME=bharatagri_iteration2
            echo SECRET_KEY=bharatagri_secure_jwt_secret_key_2026_iteration2
            echo ALGORITHM=HS256
            echo ACCESS_TOKEN_EXPIRE_MINUTES=1440
            echo PORT=5000
        )
        echo [OK] Created minimal .env.
    )
) else (
    echo [OK] Existing .env configuration preserved.
)
echo.

:: 6. MySQL & Database Check
echo [5/7] Verifying MySQL connection and BharatAgri database...
set "PYTHONPATH=%PROJECT_ROOT%"
"!VENV_PYTHON!" -c "import sys; from backend.app.core.database import check_mysql_status; sys.exit(check_mysql_status())"
set "DB_STATUS=!errorlevel!"

if "!DB_STATUS!"=="0" goto DB_OK
if "!DB_STATUS!"=="1" goto DB_CONN_ERROR
if "!DB_STATUS!"=="2" goto DB_NOT_FOUND
if "!DB_STATUS!"=="3" goto DB_EMPTY

:DB_CONN_ERROR
echo.
echo ========================================================
echo   [ERROR] MYSQL SERVICE IS NOT REACHABLE!
echo ========================================================
echo Could not connect to MySQL server on the configured port.
echo Please ensure MySQL is running [e.g. Start MySQL in XAMPP].
echo Check DB_HOST and DB_PORT settings in your .env file.
echo.
pause
exit /b 1

:DB_NOT_FOUND
echo.
echo ========================================================
echo   [ERROR] DATABASE DOES NOT EXIST!
echo ========================================================
echo The configured database was not found in MySQL.
echo.
echo Please import the schema and dataset:
echo   1. Start MySQL from XAMPP or your MySQL service.
echo   2. Create database 'bharatagri_iteration2' in MySQL or phpMyAdmin.
echo   3. Import file: database\bharatagri_iteration2.sql
echo.
set "MYSQL_CLI="
where mysql >nul 2>nul
if !errorlevel! equ 0 set "MYSQL_CLI=mysql"
if "!MYSQL_CLI!"=="" if exist "C:\xampp\mysql\bin\mysql.exe" set "MYSQL_CLI=C:\xampp\mysql\bin\mysql.exe"
if "!MYSQL_CLI!"=="" if exist "D:\xampp\mysql\bin\mysql.exe" set "MYSQL_CLI=D:\xampp\mysql\bin\mysql.exe"
if "!MYSQL_CLI!"=="" if exist "E:\xampp\mysql\bin\mysql.exe" set "MYSQL_CLI=E:\xampp\mysql\bin\mysql.exe"

if defined MYSQL_CLI (
    echo [NOTICE] Found mysql CLI client: "!MYSQL_CLI!"
    echo Attempting automatic creation and import from database\bharatagri_iteration2.sql ...
    "!VENV_PYTHON!" -c "import pymysql; from backend.app.core.config import settings; conn=pymysql.connect(host=settings.DB_HOST, port=settings.DB_PORT, user=settings.DB_USER, password=settings.DB_PASSWORD); cur=conn.cursor(); cur.execute(f'CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'); conn.close()"
    "!MYSQL_CLI!" -u root bharatagri_iteration2 < "%PROJECT_ROOT%\database\bharatagri_iteration2.sql"
    if !errorlevel! equ 0 (
        echo [OK] Database 'bharatagri_iteration2' successfully created and imported!
        goto DB_OK
    ) else (
        echo [ERROR] Automatic import failed. Please manually import database\bharatagri_iteration2.sql
        pause
        exit /b 1
    )
) else (
    pause
    exit /b 1
)

:DB_EMPTY
echo.
echo ========================================================
echo   [ERROR] DATABASE IS EMPTY - TABLES MISSING!
echo ========================================================
echo The database exists but required tables are missing.
echo Please import file: database\bharatagri_iteration2.sql
echo.
set "MYSQL_CLI="
where mysql >nul 2>nul
if !errorlevel! equ 0 set "MYSQL_CLI=mysql"
if "!MYSQL_CLI!"=="" if exist "C:\xampp\mysql\bin\mysql.exe" set "MYSQL_CLI=C:\xampp\mysql\bin\mysql.exe"
if "!MYSQL_CLI!"=="" if exist "D:\xampp\mysql\bin\mysql.exe" set "MYSQL_CLI=D:\xampp\mysql\bin\mysql.exe"
if "!MYSQL_CLI!"=="" if exist "E:\xampp\mysql\bin\mysql.exe" set "MYSQL_CLI=E:\xampp\mysql\bin\mysql.exe"

if defined MYSQL_CLI (
    echo [NOTICE] Importing database\bharatagri_iteration2.sql ...
    "!MYSQL_CLI!" -u root bharatagri_iteration2 < "%PROJECT_ROOT%\database\bharatagri_iteration2.sql"
    if !errorlevel! equ 0 (
        echo [OK] Tables imported successfully.
        goto DB_OK
    ) else (
        echo [ERROR] Import failed. Please manually import database\bharatagri_iteration2.sql
        pause
        exit /b 1
    )
) else (
    pause
    exit /b 1
)

:DB_OK
echo.

:: 7. Launch Backend API Server & Verify Reachability
echo [6/7] Starting FastAPI Backend on http://localhost:5000 ...
start "BharatAgri-Backend" "%PROJECT_ROOT%\scripts\run-backend.bat"

echo Waiting for Backend API to become reachable on http://127.0.0.1:5000/api/health ...
set "BACKEND_READY=0"
set "ATTEMPTS=0"

:HEALTH_LOOP
if !ATTEMPTS! geq 25 goto HEALTH_CHECK_DONE
set /a ATTEMPTS+=1

"!VENV_PYTHON!" -c "import urllib.request; resp=urllib.request.urlopen('http://127.0.0.1:5000/api/health', timeout=1); exit(0 if resp.status == 200 else 1)" >nul 2>nul
if !errorlevel! equ 0 (
    set "BACKEND_READY=1"
    echo [OK] Backend API is live and healthy!
    goto HEALTH_CHECK_DONE
)

ping -n 2 127.0.0.1 >nul
goto HEALTH_LOOP

:HEALTH_CHECK_DONE
if "!BACKEND_READY!"=="0" (
    echo [WARNING] Backend did not respond to /api/health within 25 seconds.
    echo Please inspect the BharatAgri-Backend console window for startup logs or errors.
)
echo.

:: 8. Launch Frontend & Open Browser
echo [7/7] Starting Vite Frontend on http://localhost:3000 ...
start "BharatAgri-Frontend" "%PROJECT_ROOT%\scripts\run-frontend.bat"

echo Waiting for Frontend dev server to initialize...
ping -n 4 127.0.0.1 >nul

echo Opening BharatAgri Portal in browser...
start http://localhost:3000

echo.
echo ========================================================
echo   BHARATAGRI ITERATION 2 IS RUNNING!
echo   Frontend : http://localhost:3000
echo   Backend  : http://localhost:5000
echo   API Docs : http://localhost:5000/docs
echo   Health   : http://localhost:5000/api/health
echo ========================================================
echo.
echo Demo Accounts (Password: BharatAgri@2026):
echo   - Farmer     : farmer@bharatagri.demo
echo   - Agent      : agent@bharatagri.demo
echo   - Centre     : centre@bharatagri.demo
echo   - Government : admin@bharatagri.demo
echo.
echo Backend and Frontend are running in separate console windows.
echo Keep those windows open while using the application.
pause
