#!/bin/bash
set -e  # Exit on any error
set -o pipefail  # Exit on error in any part of a pipeline

# Load environment variables from .env.local if it exists
if [ -f ".env.local" ]; then
    echo "Loading environment variables from .env.local..."
    export $(cat .env.local | grep -v '^#' | xargs)
fi

# Start backend in background
echo "Starting backend..."
uv run start-server &
BACKEND_PID=$!

# Check if e2e-chatbot-app-next exists, if not clone it
if [ ! -d "e2e-chatbot-app-next" ]; then
    echo "Cloning e2e-chatbot-app-next..."
    
    # Try HTTPS first, then SSH as fallback
    if git clone --filter=blob:none --sparse https://github.com/databricks/app-templates.git temp-app-templates 2>/dev/null; then
        echo "Cloned using HTTPS"
    elif git clone --filter=blob:none --sparse git@github.com:databricks/app-templates.git temp-app-templates 2>/dev/null; then
        echo "Cloned using SSH"
    else
        echo "ERROR: Failed to clone repository."
        echo "Please manually download the folder from:"
        echo "  https://download-directory.github.io/?url=https://github.com/databricks/app-templates/tree/main/e2e-chatbot-app-next"
        echo "Then unzip it in this directory and re-run `./scripts/start-app.sh`."
        exit 1
    fi
    
    cd temp-app-templates
    git sparse-checkout set e2e-chatbot-app-next
    cd ..
    mv temp-app-templates/e2e-chatbot-app-next .
    rm -rf temp-app-templates
fi

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

# Wait for any process to exit
wait -n

# Capture the exit code of the first process that exits
EXIT_CODE=$?

# If any process failed, kill the others and exit with that code
if [ $EXIT_CODE -ne 0 ]; then
    echo "ERROR: One of the processes exited with code $EXIT_CODE"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit $EXIT_CODE
fi

# If we get here, a process exited successfully (unusual for servers)
# Kill the other and exit
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
exit 0
