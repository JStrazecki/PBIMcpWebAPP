#!/bin/bash
# Azure App Service startup script for FastMCP

echo "Starting FastMCP Power BI Server..."
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Environment: Azure App Service"

# Install dependencies if needed
if [ -f requirements.txt ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Set environment variable for transport
export MCP_TRANSPORT=http

# Start the server with gunicorn
echo "Starting gunicorn with FastMCP + Flask..."
exec gunicorn --bind=0.0.0.0:$PORT \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 600 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    asgi_azure:app