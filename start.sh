#!/bin/bash

# Lifetime Calendar - Development Startup Script

echo "🗓️  Starting Lifetime Calendar Application"
echo "========================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is required but not installed."
    exit 1
fi

echo "✅ All prerequisites satisfied"

# Start backend
echo ""
echo "Starting backend server..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
if [ ! -f ".requirements_installed" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    touch .requirements_installed
fi

# Start backend in background
echo "Starting FastAPI server on http://localhost:8000"
python main.py &
BACKEND_PID=$!

# Go back to root directory
cd ..

# Start frontend
echo ""
echo "Starting frontend server..."
cd frontend

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Start frontend in background
echo "Starting Vue.js development server on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

# Wait for servers to start
sleep 3

echo ""
echo "🎉 Application started successfully!"
echo ""
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Servers stopped. Goodbye! 👋"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait