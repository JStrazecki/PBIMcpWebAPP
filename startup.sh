#!/bin/bash
# Azure App Service startup script for FastMCP

echo "Starting FastMCP Power BI Server..."
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# Install dependencies if needed
if [ -f requirements.txt ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Try different approaches based on what works

# Approach 1: Try gunicorn with ASGI wrapper
echo "Attempting to start with gunicorn..."
gunicorn --bind=0.0.0.0:$PORT \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 600 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    asgi:app &

# Give it time to start
sleep 10

# Check if gunicorn started successfully
if pgrep -f gunicorn > /dev/null; then
    echo "Gunicorn started successfully"
    wait
else
    echo "Gunicorn failed to start, trying direct FastMCP run..."
    # Approach 2: Direct run
    python run_fastmcp.py
fi