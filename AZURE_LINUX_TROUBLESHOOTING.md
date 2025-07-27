# Azure Web App Linux Python Deployment Troubleshooting Guide

## The Problem
Your Python 3.13 Flask app deploys successfully but Azure Web App Linux container defaults to .NET Core instead of executing your Python startup command.

## Root Cause Analysis
Azure Web App Linux uses **Oryx build system** and **container detection logic** that sometimes fails to properly execute Python startup commands, especially when:
- Multiple runtime stacks are detected
- Startup command execution fails silently
- Container health checks don't pass

## Step-by-Step Linux Container Fixes

### Step 1: Force Python Runtime Detection
Add these files to ensure Azure detects Python correctly:

```bash
# In Azure SSH console (/home/site/wwwroot):
echo "python-3.13" > runtime.txt
echo "python" > .platform/platform.txt
```

### Step 2: Fix Virtual Environment Path
Azure Oryx creates virtual environment at `/home/site/wwwroot/antenv`. Verify it exists:

```bash
# Check virtual environment
ls -la /home/site/wwwroot/antenv/
ls -la /home/site/wwwroot/antenv/bin/

# If missing, Oryx build failed - check deployment logs
```

### Step 3: Manual Python App Testing
Test your app manually in Azure SSH:

```bash
# Connect to Azure SSH console
cd /home/site/wwwroot

# Activate virtual environment
source antenv/bin/activate

# Test Python and imports
python3 --version
python3 -c "import sys; print(sys.path)"
python3 -c "from app import APP; print('Import successful')"

# Test gunicorn directly
gunicorn --version
which gunicorn

# Start app manually (for testing)
gunicorn --bind=0.0.0.0:8000 --workers 1 --timeout 600 app:APP
```

### Step 4: Check Process and Port Status
```bash
# Check what's running on ports
netstat -tulpn | grep :8000
netstat -tulpn | grep :8181

# Check running processes
ps aux | grep python
ps aux | grep gunicorn
ps aux | grep dotnet

# Kill any conflicting processes
pkill -f gunicorn
pkill -f dotnet
```

### Step 5: Fix Container Startup Script
Create a more robust startup script:

```bash
# Create /home/site/wwwroot/startup_fix.sh
#!/bin/bash
set -e  # Exit on any error

echo "=== AZURE LINUX PYTHON STARTUP ==="
echo "Timestamp: $(date)"
echo "Working directory: $(pwd)"
echo "Python version: $(python3 --version)"

# Kill any existing processes
pkill -f gunicorn || true
pkill -f dotnet || true

# Ensure we're in the right directory
cd /home/site/wwwroot

# Check virtual environment
if [ ! -d "antenv" ]; then
    echo "ERROR: Virtual environment 'antenv' not found"
    echo "Available directories:"
    ls -la
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source antenv/bin/activate

# Verify activation
echo "Python location: $(which python3)"
echo "Pip location: $(which pip)"
echo "Gunicorn location: $(which gunicorn)"

# Test app import
echo "Testing app import..."
python3 -c "from app import APP; print('✓ APP imported successfully')" || {
    echo "✗ Failed to import APP"
    exit 1
}

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn \
    --bind=0.0.0.0:8000 \
    --workers=1 \
    --timeout=600 \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=info \
    --preload \
    app:APP
```

### Step 6: Update Azure Startup Command
In Azure Portal → Configuration → General Settings:

**Option A - Direct Script:**
```bash
bash /home/site/wwwroot/startup_fix.sh
```

**Option B - Inline Command:**
```bash
cd /home/site/wwwroot && source antenv/bin/activate && exec gunicorn --bind=0.0.0.0:8000 --workers=1 --timeout=600 --preload app:APP
```

**Option C - Force Kill and Restart:**
```bash
pkill -f dotnet || true; cd /home/site/wwwroot && source antenv/bin/activate && exec gunicorn --bind=0.0.0.0:8000 --workers=1 --timeout=600 app:APP
```

### Step 7: Application Settings to Add
In Azure Portal → Configuration → Application Settings:

| Setting | Value | Purpose |
|---------|-------|---------|
| `WEBSITES_ENABLE_APP_SERVICE_STORAGE` | `true` | Enable persistent storage |
| `WEBSITES_CONTAINER_START_TIME_LIMIT` | `1800` | Increase startup timeout |
| `PORT` | `8000` | Explicitly set port |
| `WEBSITE_HTTPLOGGING_RETENTION_DAYS` | `7` | Keep logs longer |
| `ORYX_BUILD_ENABLED` | `true` | Force Oryx build |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Build during deployment |

### Step 8: Debug Container Health
Check if your app is actually starting but failing health checks:

```bash
# In Azure SSH, test app endpoint
curl http://localhost:8000/
curl http://localhost:8000/health

# Check app logs
tail -f /var/log/webapp_output.log
tail -f /appsvctmp/volatile/logs/runtime/container.log
```

### Step 9: Alternative Approaches

#### Option A: Use Dockerfile (Recommended)
Create `Dockerfile` in your repo:
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "--bind=0.0.0.0:8000", "--workers=1", "--timeout=600", "app:APP"]
```

#### Option B: Use Docker Compose
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
```

#### Option C: Switch to Azure Container Instances
If Web App continues failing, consider:
1. Build Docker image locally
2. Push to Azure Container Registry
3. Deploy to Azure Container Instances

### Step 10: Expected Success Output
When working correctly, you should see:
```log
=== AZURE LINUX PYTHON STARTUP ===
Timestamp: Mon Jul 27 21:30:00 UTC 2025
Python version: Python 3.13.5
Activating virtual environment...
✓ APP imported successfully
Starting gunicorn...
[2025-07-27 21:30:01] Starting gunicorn 23.0.0
[2025-07-27 21:30:01] Listening at: http://0.0.0.0:8000 (1)
[2025-07-27 21:30:01] Using worker: sync
[2025-07-27 21:30:01] Booting worker with pid: 123
```

## Common Issues and Solutions

### Issue: "antenv not found"
**Solution**: Oryx build failed. Check deployment logs and fix `.deployment` file.

### Issue: "Module 'app' not found"
**Solution**: Ensure `app.py` exists and contains `APP = app` export.

### Issue: "Port 8000 already in use"
**Solution**: Kill existing processes: `pkill -f gunicorn`

### Issue: Container keeps restarting
**Solution**: Add health check endpoint and increase startup timeout.

### Issue: .NET Core still starting
**Solution**: Remove any `.csproj`, `web.config`, or .NET files that confuse detection.

## Emergency Nuclear Option
If all else fails:
1. Delete the Web App
2. Create new Web App with Docker container option
3. Use custom Dockerfile approach
4. This guarantees Python execution without Azure's auto-detection issues

## Next Steps
1. Try Step 5 (robust startup script) first
2. If that fails, try Step 9A (Dockerfile approach)
3. If still failing, contact me with latest logs for advanced debugging

Remember: The issue is NOT your Python code - it's Azure Web App Linux container startup logic.