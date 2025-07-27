#!/bin/bash
# Startup script for Azure App Service - Power BI MCP Finance Server
# This script configures and starts the Python application on Azure Linux App Service

echo "=== Power BI MCP Finance Server Startup ==="
echo "Starting at: $(date)"

# Set environment variables for Azure App Service
export PYTHONPATH="/home/site/wwwroot:$PYTHONPATH"
export PYTHONUNBUFFERED=1

# Azure App Service provides PORT environment variable
export PORT=${PORT:-8000}

# Set default authentication port if not specified
export AUTH_PORT=${AUTH_PORT:-$PORT}

echo "Python path: $PYTHONPATH"
echo "Server port: $PORT"
echo "Auth port: $AUTH_PORT"

# Navigate to application directory
cd /home/site/wwwroot

# Check if virtual environment exists and activate it
if [ -d "antenv" ]; then
    echo "Activating virtual environment..."
    source antenv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "No virtual environment found, using system Python"
fi

# Install dependencies - prioritize simplified requirements
if [ -f "requirements_simple.txt" ]; then
    echo "Installing simplified Python dependencies (no database)..."
    pip install --no-cache-dir -r requirements_simple.txt
elif [ -f "requirements.txt" ]; then
    echo "Installing full Python dependencies..."
    pip install --no-cache-dir -r requirements.txt
else
    echo "Warning: No requirements file found"
fi

# Check if the main application file exists
if [ -f "main_simple.py" ]; then
    MAIN_MODULE="main_simple"
    echo "Using simplified main module (no database dependencies)"
elif [ -f "pbi_mcp_finance/main.py" ]; then
    MAIN_MODULE="pbi_mcp_finance.main"
    echo "Using full main module (with database dependencies)"
elif [ -f "main.py" ]; then
    MAIN_MODULE="main"
else
    echo "Error: Cannot find main application file"
    exit 1
fi

echo "Main module: $MAIN_MODULE"

# Check authentication configuration
if [ "$AUTH_ENABLED" = "true" ]; then
    echo "🔐 Authentication enabled"
    if [ -z "$AZURE_CLIENT_ID" ] || [ -z "$AZURE_CLIENT_SECRET" ] || [ -z "$AZURE_TENANT_ID" ]; then
        echo "⚠️  Warning: Authentication enabled but Azure AD credentials not configured"
        echo "Required environment variables: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID"
    else
        echo "✅ Azure AD authentication configured"
    fi
else
    echo "🔓 Authentication disabled"
fi

# Check Power BI configuration
if [ -z "$POWERBI_TOKEN" ] && ([ -z "$POWERBI_CLIENT_ID" ] || [ -z "$POWERBI_CLIENT_SECRET" ]); then
    echo "⚠️  Warning: Power BI authentication not configured"
    echo "Set either POWERBI_TOKEN or POWERBI_CLIENT_ID + POWERBI_CLIENT_SECRET"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Set up logging
export LOG_LEVEL=${LOG_LEVEL:-INFO}
echo "Log level: $LOG_LEVEL"

# Start the application
echo "🚀 Starting Power BI MCP Finance Server..."
echo "Listening on port: $PORT"
echo "================================================"

# Use gunicorn for production deployment with proper Azure App Service integration
if command -v gunicorn &> /dev/null; then
    echo "Starting with Gunicorn..."
    exec gunicorn \
        --bind "0.0.0.0:$PORT" \
        --workers 1 \
        --threads 4 \
        --timeout 300 \
        --keep-alive 2 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --access-logfile "-" \
        --error-logfile "-" \
        --log-level info \
        --worker-class sync \
        "$MAIN_MODULE:app"
else
    echo "Gunicorn not found, starting with Python directly..."
    # Fallback to direct Python execution
    exec python -m $MAIN_MODULE
fi