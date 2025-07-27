#!/bin/bash
# Emergency startup script that forces Python app execution
echo "=== EMERGENCY PYTHON APP STARTUP ==="
echo "Starting: $(date)"

cd /home/site/wwwroot

# Activate virtual environment if it exists
if [ -d "antenv" ]; then
    echo "Activating virtual environment..."
    source antenv/bin/activate
fi

echo "Python location: $(which python3)"
echo "Gunicorn location: $(which gunicorn)"

# Test app import
echo "Testing app import..."
python3 -c "from app import APP; print('APP imported successfully')" || {
    echo "FAILED to import APP"
    exit 1
}

# Start the application
echo "Starting gunicorn with APP..."
exec gunicorn --bind=0.0.0.0:8000 --workers 1 --timeout 600 --access-logfile - --error-logfile - --log-level info app:APP