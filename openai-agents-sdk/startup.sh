#!/bin/bash

# Start backend in background
echo "Starting backend..."
uv run start-server &
BACKEND_PID=$!

# Start frontend in background
echo "Starting frontend..."
cd e2e-chatbot-app-next
npm install
npm run build
npm run start &
FRONTEND_PID=$!

# Function to cleanup processes on script exit
cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Trap cleanup function on script termination
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait
