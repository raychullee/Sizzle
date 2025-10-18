#!/bin/bash
# Master startup script for Sizzle app
# This script starts both the frontend and backend components

# Stop any existing instances
echo "Stopping any existing processes..."
pkill -f "npm run dev" || true
pkill -f "python.*app.py" || true
pkill -f "uvicorn app:app" || true

# Setup and start backend
echo "Setting up backend..."
cd "$(dirname "$0")/backend"

# Create/update virtualenv if not exists
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing backend dependencies..."
pip install -r requirements.txt

# Start backend server
echo "Starting backend server..."
echo "API will be available at http://localhost:8000"
python app.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 5

# Setup and start frontend
echo "Starting frontend..."
cd "$(dirname "$0")/frontend"
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo ""
echo "Sizzle application started!"
echo "Access the application at: http://localhost:3000"
echo ""
echo "To view logs:"
echo "  Backend logs: tail -f $(dirname "$0")/backend/backend.log"
echo "  Frontend logs: tail -f $(dirname "$0")/frontend/frontend.log"
echo ""
echo "To stop the application:"
echo "  kill -9 $BACKEND_PID $FRONTEND_PID"
echo ""
