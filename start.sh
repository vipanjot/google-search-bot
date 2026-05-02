#!/bin/bash
set -e

echo "=== Search Bot UI Startup ==="

# Install Python deps
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Install frontend deps
echo "Installing frontend dependencies..."
cd frontend
npm install --silent
cd ..

# Start backend
echo "Starting backend on http://localhost:8000 ..."
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

sleep 2

# Start frontend
echo "Starting frontend on http://localhost:5173 ..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait
