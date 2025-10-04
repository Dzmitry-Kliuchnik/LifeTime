@echo off
setlocal enabledelayedexpansion

REM Lifetime Calendar - Development Startup Script for Windows

echo.
echo 🗓️  Starting Lifetime Calendar Application
echo ========================================
echo.

REM Check prerequisites
echo Checking prerequisites...

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3 is required but not installed.
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Check for Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is required but not installed.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check for npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm is required but not installed.
    pause
    exit /b 1
)

echo ✅ All prerequisites satisfied
echo.

REM Start backend
echo Starting backend server...
cd backend

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements if needed
if not exist ".requirements_installed" (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    echo. > .requirements_installed
)

REM Start backend in new window
echo Starting FastAPI server on http://localhost:8000
start "Lifetime Calendar - Backend" cmd /c "python main.py"

REM Give backend time to start
timeout /t 2 /nobreak >nul

REM Go back to root directory
cd ..

REM Start frontend
echo.
echo Starting frontend server...
cd frontend

REM Install npm dependencies if needed
if not exist "node_modules\" (
    echo Installing npm dependencies...
    call npm install
)

REM Start frontend in new window
echo Starting Vue.js development server on http://localhost:5173
start "Lifetime Calendar - Frontend" cmd /c "npm run dev"

REM Wait for servers to start
timeout /t 3 /nobreak >nul

echo.
echo 🎉 Application started successfully!
echo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Both servers are running in separate windows.
echo Close those windows or press Ctrl+C in them to stop the servers.
echo.
echo You can now close this window.
echo.
