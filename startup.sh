#!/bin/bash
# Startup script for Azure App Service - Power BI MCP Finance Server
# This script configures and starts the Python application on Azure Linux App Service

echo "=== Power BI MCP Finance Server Startup ==="
echo "Starting at: $(date)"
echo "Working directory: $(pwd)"
echo "Files in directory: $(ls -la)"

# Set environment variables for Azure App Service
export PYTHONPATH="/home/site/wwwroot:$PYTHONPATH"
export PYTHONUNBUFFERED=1

# Azure App Service provides PORT environment variable
export PORT=${PORT:-8000}

echo "Python path: $PYTHONPATH"
echo "Server port: $PORT"
echo "Python version: $(python3 --version)"
echo "Python location: $(which python3)"

# Navigate to application directory
cd /home/site/wwwroot

# Azure Oryx creates virtual environment at /home/site/wwwroot/antenv
if [ -d "antenv" ]; then
    echo "Activating Oryx virtual environment..."
    source antenv/bin/activate
    echo "Virtual environment activated: $(which python)"
    echo "Pip packages installed:"
    pip list | grep -E "(flask|gunicorn|fastmcp)"
else
    echo "No virtual environment found, using system Python"
fi

# Verify required files exist
echo "Checking for main application file..."
if [ -f "main_simple.py" ]; then
    MAIN_MODULE="main_simple"
    echo "✅ Found main_simple.py - using simplified module"
else
    echo "❌ Error: main_simple.py not found"
    echo "Available Python files:"
    ls -la *.py 2>/dev/null || echo "No Python files found"
    exit 1
fi

# Verify the app can be imported
echo "Testing application import..."
python3 -c "from $MAIN_MODULE import app; print('✅ App imported successfully')" || {
    echo "❌ Failed to import application"
    exit 1
}

# Check Power BI configuration
echo "Checking Power BI configuration..."
if [ -z "$POWERBI_TOKEN" ] && ([ -z "$POWERBI_CLIENT_ID" ] || [ -z "$POWERBI_CLIENT_SECRET" ]); then
    echo "⚠️  Warning: Power BI authentication not configured"
    echo "Set either POWERBI_TOKEN or POWERBI_CLIENT_ID + POWERBI_CLIENT_SECRET"
else
    echo "✅ Power BI configuration found"
fi

# Create logs directory
mkdir -p logs

# Set up logging
export LOG_LEVEL=${LOG_LEVEL:-INFO}
echo "Log level: $LOG_LEVEL"

# Start the application
echo "🚀 Starting Power BI MCP Finance Server..."
echo "Listening on port: $PORT"
echo "Module: $MAIN_MODULE"
echo "================================================"

# Use gunicorn for production deployment
echo "Starting with Gunicorn..."
exec gunicorn \
    --bind "0.0.0.0:$PORT" \
    --workers 1 \
    --timeout 600 \
    --access-logfile "-" \
    --error-logfile "-" \
    --log-level info \
    --preload \
    "$MAIN_MODULE:app"