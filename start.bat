@echo off
setlocal enabledelayedexpansion

:: ========================================================
::       BHARATAGRI ITERATION 2 - STARTUP LAUNCHER
:: ========================================================

:: 1. Project path: Must work when extracted anywhere, including folders with spaces
cd /d "%~dp0"
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo ========================================================
echo       BHARATAGRI ITERATION 2 - STARTUP LAUNCHER
echo ========================================================
echo Project Directory: "%PROJECT_ROOT%"
echo.

:: 2. Python Environment Detection
echo [1/7] Detecting Python environment...
set "VENV_DIR="
set "VENV_PYTHON="

if exist "%PROJECT_ROOT%\venv\Scripts\python.exe" (
    set "VENV_DIR=%PROJECT_ROOT%\venv"
    set "VENV_PYTHON=%PROJECT_ROOT%\venv\Scripts\python.exe"
    goto PYTHON_DETECTED
)

if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    set "VENV_DIR=%PROJECT_ROOT%\.venv"
    set "VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
    goto PYTHON_DETECTED
)

set "PYTHON_EXE="
where python >nul 2>nul
if !errorlevel! equ 0 set "PYTHON_EXE=python"
if not defined PYTHON_EXE (
    where py >nul 2>nul
    if !errorlevel! equ 0 set "PYTHON_EXE=py -3"
)

if not defined PYTHON_EXE (
    echo [ERROR] Python was not found in PATH or project directory.
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure "Add Python to PATH" is checked during installation.
    pause
    exit /b 1
)

echo [NOTICE] Virtual environment not found. Creating .venv ...
!PYTHON_EXE! -m venv "%PROJECT_ROOT%\.venv"
if !errorlevel! neq 0 (
    echo [ERROR] Failed to create virtual environment in .venv.
    pause
    exit /b 1
)
set "VENV_DIR=%PROJECT_ROOT%\.venv"
set "VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
echo [OK] Virtual environment created at .venv.

:PYTHON_DETECTED
for /f "tokens=*" %%v in ('"%VENV_PYTHON%" --version 2^>^&1') do echo [OK] Found Python: %%v
echo [OK] Using Python executable: "!VENV_PYTHON!"
echo.

:: 3. Python Dependencies Verification
echo [2/7] Verifying Python dependencies...
"!VENV_PYTHON!" -c "import fastapi, uvicorn, sqlalchemy, pymysql, xgboost, ortools, jose, bcrypt"
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

:: 4. Node.js and npm Detection and Frontend Dependencies
echo [3/7] Detecting Node.js and frontend dependencies...
where node >nul 2>nul
if !errorlevel! neq 0 (
    if exist "%USERPROFILE%\.local\node\node.exe" (
        set "PATH=%USERPROFILE%\.local\node;!PATH!"
    ) else if exist "C:\Program Files\nodejs\node.exe" (
        set "PATH=C:\Program Files\nodejs;!PATH!"
    )
)

where node >nul 2>nul
if !errorlevel! neq 0 (
    echo [ERROR] Node.js is not found in PATH or standard installation locations.
    echo Please install Node.js 18+ from https://nodejs.org/ to run the frontend.
    pause
    exit /b 1
)

where npm >nul 2>nul
if !errorlevel! neq 0 (
    if exist "%USERPROFILE%\.local\node\npm.cmd" (
        set "PATH=%USERPROFILE%\.local\node;!PATH!"
    ) else if exist "C:\Program Files\nodejs\npm.cmd" (
        set "PATH=C:\Program Files\nodejs;!PATH!"
    ) else if exist "%APPDATA%\npm\npm.cmd" (
        set "PATH=%APPDATA%\npm;!PATH!"
    )
)

where npm >nul 2>nul
if !errorlevel! neq 0 (
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
        copy "%PROJECT_ROOT%\.env.example" "%PROJECT_ROOT%\.env"
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

:: 6. MySQL and Database Check (Non-blocking: warn instead of crashing)
echo [5/7] Verifying MySQL connection and BharatAgri database...
set "PYTHONPATH=%PROJECT_ROOT%"
"!VENV_PYTHON!" -c "import sys; from backend.app.core.database import check_mysql_status; sys.exit(check_mysql_status())"
set "DB_STATUS=!errorlevel!"

if "!DB_STATUS!"=="0" (
    echo [OK] MySQL database is connected and populated.
    goto DB_CHECK_DONE
)

if "!DB_STATUS!"=="1" (
    echo.
    echo --------------------------------------------------------
    echo [WARNING] MySQL service is not reachable on localhost:3306.
    echo           Please ensure MySQL is running, e.g. Start MySQL in XAMPP.
    echo [NOTICE]  Continuing startup: Backend and Frontend will still run.
    echo           Database queries will report connection errors until MySQL is started.
    echo --------------------------------------------------------
    goto DB_CHECK_DONE
)

if "!DB_STATUS!"=="2" (
    echo.
    echo --------------------------------------------------------
    echo [WARNING] Database 'bharatagri_iteration2' does not exist in MySQL.
    echo Attempting automatic creation and import from database\bharatagri_iteration2.sql ...
    set "MYSQL_CLI="
    where mysql >nul 2>nul
    if !errorlevel! equ 0 set "MYSQL_CLI=mysql"
    if "!MYSQL_CLI!"=="" if exist "C:\xampp\mysql\bin\mysql.exe" set "MYSQL_CLI=C:\xampp\mysql\bin\mysql.exe"
    if "!MYSQL_CLI!"=="" if exist "D:\xampp\mysql\bin\mysql.exe" set "MYSQL_CLI=D:\xampp\mysql\bin\mysql.exe"
    if "!MYSQL_CLI!"=="" if exist "E:\xampp\mysql\bin\mysql.exe" set "MYSQL_CLI=E:\xampp\mysql\bin\mysql.exe"

    if defined MYSQL_CLI (
        "!VENV_PYTHON!" -c "import pymysql; from backend.app.core.config import settings; conn=pymysql.connect(host=settings.DB_HOST, port=settings.DB_PORT, user=settings.DB_USER, password=settings.DB_PASSWORD); cur=conn.cursor(); cur.execute(f'CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'); conn.close()"
        "!MYSQL_CLI!" -u root bharatagri_iteration2 < "%PROJECT_ROOT%\database\bharatagri_iteration2.sql"
        if !errorlevel! equ 0 (
            echo [OK] Database 'bharatagri_iteration2' created and imported successfully!
        ) else (
            echo [WARNING] Automatic import failed. Please manually import database\bharatagri_iteration2.sql
        )
    ) else (
        echo [WARNING] mysql CLI client not found. Please manually import database\bharatagri_iteration2.sql
    )
    echo --------------------------------------------------------
    goto DB_CHECK_DONE
)

if "!DB_STATUS!"=="3" (
    echo.
    echo --------------------------------------------------------
    echo [WARNING] Database exists but tables are missing.
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
        ) else (
            echo [WARNING] Import failed. Please manually import database\bharatagri_iteration2.sql
        )
    ) else (
        echo [WARNING] Please manually import database\bharatagri_iteration2.sql into MySQL.
    )
    echo --------------------------------------------------------
    goto DB_CHECK_DONE
)

:DB_CHECK_DONE
echo.

:: 7. Launch Backend API Server and Verify Reachability
echo [6/7] Checking backend port (5000) and starting FastAPI server...
set "PORT_5000_IN_USE=0"
set "BACKEND_ALREADY_HEALTHY=0"

"!VENV_PYTHON!" -c "import socket; s=socket.socket(); res=s.connect_ex(('127.0.0.1', 5000)); s.close(); exit(0 if res==0 else 1)"
if !errorlevel! equ 0 set "PORT_5000_IN_USE=1"

if "!PORT_5000_IN_USE!"=="1" (
    "!VENV_PYTHON!" -c "import urllib.request; resp=urllib.request.urlopen('http://127.0.0.1:5000/api/health', timeout=2); exit(0 if resp.status==200 else 1)" 2>nul
    if !errorlevel! equ 0 (
        set "BACKEND_ALREADY_HEALTHY=1"
        echo [OK] Backend API is already running and healthy on http://localhost:5000
        goto BACKEND_LAUNCH_DONE
    ) else (
        echo [WARNING] Port 5000 is occupied by another process:
        netstat -ano | findstr /R /C:":5000 .*LISTENING"
        echo [NOTICE] Attempting to launch backend anyway. If it fails, please free port 5000.
    )
)

echo Starting FastAPI Backend in separate window...
start "BharatAgri-Backend" cmd /k "call "%PROJECT_ROOT%\scripts\run-backend.bat""

echo Waiting for Backend API to become reachable on http://127.0.0.1:5000/api/health ...
set "BACKEND_READY=0"
set "ATTEMPTS=0"

:BACKEND_POLL_LOOP
if !ATTEMPTS! geq 30 goto BACKEND_POLL_DONE
set /a ATTEMPTS+=1

"!VENV_PYTHON!" -c "import urllib.request; resp=urllib.request.urlopen('http://127.0.0.1:5000/api/health', timeout=1); exit(0 if resp.status == 200 else 1)" 2>nul
if !errorlevel! equ 0 (
    set "BACKEND_READY=1"
    echo [OK] Backend API is live and healthy!
    goto BACKEND_POLL_DONE
)

ping -n 2 127.0.0.1 >nul
goto BACKEND_POLL_LOOP

:BACKEND_POLL_DONE
if "!BACKEND_READY!"=="0" (
    echo.
    echo [ERROR] Backend did not respond on http://127.0.0.1:5000/api/health within 30 seconds.
    echo [ERROR] Please inspect the "BharatAgri-Backend" console window for traceback or errors.
    echo Direct connection test:
    "!VENV_PYTHON!" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/health', timeout=2)"
)

:BACKEND_LAUNCH_DONE
echo.

:: 8. Launch Frontend and Wait for Reachability Before Opening Browser
echo [7/7] Checking frontend port (3000) and starting Vite dev server...
set "PORT_3000_IN_USE=0"
set "FRONTEND_ALREADY_HEALTHY=0"

"!VENV_PYTHON!" -c "import socket; s=socket.socket(); res=s.connect_ex(('127.0.0.1', 3000)); s.close(); exit(0 if res==0 else 1)"
if !errorlevel! equ 0 set "PORT_3000_IN_USE=1"

if "!PORT_3000_IN_USE!"=="1" (
    "!VENV_PYTHON!" -c "import urllib.request; resp=urllib.request.urlopen('http://localhost:3000', timeout=2); exit(0 if resp.status==200 else 1)" 2>nul
    if !errorlevel! equ 0 (
        set "FRONTEND_ALREADY_HEALTHY=1"
        echo [OK] Frontend dev server is already running on http://localhost:3000
        goto FRONTEND_LAUNCH_DONE
    ) else (
        echo [WARNING] Port 3000 is occupied by another process:
        netstat -ano | findstr /R /C:":3000 .*LISTENING"
    )
)

echo Starting Vite Frontend in separate window...
start "BharatAgri-Frontend" cmd /k "call "%PROJECT_ROOT%\scripts\run-frontend.bat""

echo Waiting for Frontend dev server to become reachable on http://localhost:3000 ...
set "FRONTEND_READY=0"
set "ATTEMPTS=0"

:FRONTEND_POLL_LOOP
if !ATTEMPTS! geq 30 goto FRONTEND_POLL_DONE
set /a ATTEMPTS+=1

"!VENV_PYTHON!" -c "import urllib.request; resp=urllib.request.urlopen('http://localhost:3000', timeout=1); exit(0 if resp.status == 200 else 1)" 2>nul
if !errorlevel! equ 0 (
    set "FRONTEND_READY=1"
    echo [OK] Frontend dev server is live on http://localhost:3000!
    goto FRONTEND_POLL_DONE
)

ping -n 2 127.0.0.1 >nul
goto FRONTEND_POLL_LOOP

:FRONTEND_POLL_DONE
if "!FRONTEND_READY!"=="0" (
    echo.
    echo [ERROR] Frontend did not respond on http://localhost:3000 within 30 seconds.
    echo [ERROR] Please inspect the "BharatAgri-Frontend" console window for Vite error logs.
)

:FRONTEND_LAUNCH_DONE

:: 9. Open Browser and Display Summary
echo.
echo Opening BharatAgri Portal in browser: http://localhost:3000 ...
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
