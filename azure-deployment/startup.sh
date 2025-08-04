#!/bin/bash
# startup.sh - PBI MCP Bot Startup Script

echo "=== PBI MCP Bot Startup ==="
echo "Time: $(date)"
echo "Directory: $(pwd)"
echo "Running PBI MCP Assistant"

cd /home/site/wwwroot

# Use Python 3.11 (matching the working example approach)
export PATH="/opt/python/3.11.12/bin:/opt/python/3.11/bin:$PATH"
export PYTHONPATH="/home/site/wwwroot:$PYTHONPATH"

echo "Python: $(which python3)"
echo "Python version: $(python3 --version)"

# Install packages if not already installed (FastMCP check)
if [ ! -d "/home/.local/lib/python3.11/site-packages/fastmcp" ]; then
    echo "Installing packages..."
    python3 -m pip install --user --upgrade pip
    python3 -m pip install --user -r requirements.txt
else
    echo "Packages already installed, skipping installation"
fi

# Add user site-packages to Python path (critical from working example)
export PATH="$PATH:/home/.local/bin"
export PYTHONPATH="$PYTHONPATH:/home/.local/lib/python3.11/site-packages"

# Verify core packages (including FastMCP)
echo "Verifying packages..."
python3 -c "import fastmcp; print('✓ fastmcp installed')" || exit 1
python3 -c "import flask; print('✓ flask installed')" || exit 1
python3 -c "import msal; print('✓ msal installed')" || exit 1
python3 -c "import requests; print('✓ requests installed')" || exit 1
python3 -c "import gunicorn; print('✓ gunicorn installed')" || exit 1
python3 -c "import uvicorn; print('✓ uvicorn installed')" || exit 1

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p .cache

# Verify main app loads (Flask MCP server)
echo "Testing Flask MCP server import..."
python3 -c "import mcp_simple_server; print('✓ Flask MCP server loads successfully')" || exit 1

# Start the Flask MCP server directly
PORT=${PORT:-8000}
echo "Starting Flask MCP Server on port $PORT..."
exec python3 mcp_simple_server.py