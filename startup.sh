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

# Install packages if not already installed (like the working example)
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

# Verify core packages (like the working example)
echo "Verifying packages..."
python3 -c "import fastmcp; print('✓ fastmcp installed')" || exit 1
python3 -c "import flask; print('✓ flask installed')" || exit 1
python3 -c "import msal; print('✓ msal installed')" || exit 1
python3 -c "import requests; print('✓ requests installed')" || exit 1
python3 -c "import gunicorn; print('✓ gunicorn installed')" || exit 1

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p .cache

# Verify main app loads (exactly like working example)
echo "Testing main app import..."
python3 -c "from app import APP; print('✓ PBI MCP app loads successfully')" || exit 1

# Start the app (using the exact same pattern as working example)
echo "Starting PBI MCP Bot on port 8000..."
exec python3 -m gunicorn --bind 0.0.0.0:8000 --worker-class sync --timeout 600 --workers 1 app:APP