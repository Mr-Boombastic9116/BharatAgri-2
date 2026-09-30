#!/usr/bin/env bash
set -e

echo "========================================================"
echo "      BHARATAGRI ITERATION 2 - LOCAL STARTUP (SH)"
echo "========================================================"
echo ""

# 1. Check Python
echo "[1/8] Checking Python..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH!"
    exit 1
fi
PYTHON_BIN=$(command -v python3 || command -v python)
$PYTHON_BIN --version
echo "[OK] Python is available."
echo ""

# 2. Check Node / npm
echo "[2/8] Checking Node.js and npm..."
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo "[ERROR] Node.js or npm is not installed or not in PATH!"
    exit 1
fi
node --version
npm --version
echo "[OK] Node and npm are available."
echo ""

# 3. Check MySQL port
echo "[3/8] Checking MySQL connection on port 3306..."
if command -v nc &> /dev/null; then
    if nc -z localhost 3306 2>/dev/null; then
        echo "[OK] MySQL is active on port 3306."
    else
        echo "[WARNING] Port 3306 is not open. Ensure MySQL / MariaDB is running!"
    fi
else
    echo "[INFO] nc not found; skipping direct port check. Ensure MySQL is running on port 3306."
fi
echo ""

# 4. Check .env
echo "[4/8] Checking .env configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Copying .env.example to .env..."
        cp .env.example .env
        echo "[OK] Created .env with default settings."
    else
        echo "[ERROR] Neither .env nor .env.example found!"
        exit 1
    fi
else
    echo "[OK] .env configuration file exists."
fi
echo ""

# 5. Check dependencies
echo "[5/8] Verifying Python requirements..."
$PYTHON_BIN -c "import fastapi, sqlalchemy, pymysql, xgboost, ortools" 2>/dev/null || {
    echo "Installing missing requirements..."
    $PYTHON_BIN -m pip install -r requirements.txt
}
echo "[OK] Python dependencies verified."
echo ""

# 6. Start Backend in background
echo "[6/8] Starting FastAPI Backend on port 5000..."
export PYTHONPATH="."
$PYTHON_BIN -m uvicorn backend.app.main:app --host 0.0.0.0 --port 5000 --reload &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID"
sleep 2
echo ""

# 7. Start Frontend in background
echo "[7/8] Starting Vite Frontend on port 3000..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..
sleep 3
echo ""

# 8. Open browser
echo "[8/8] Opening browser..."
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 &
elif command -v open &> /dev/null; then
    open http://localhost:3000 &
fi

echo "========================================================"
echo "  BharatAgri Iteration 2 is running!"
echo "  Frontend : http://localhost:3000"
echo "  Backend  : http://localhost:5000"
echo "  API Docs : http://localhost:5000/docs"
echo "========================================================"
echo "Press Ctrl+C to terminate both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
