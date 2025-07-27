# Azure Startup Debug Checklist

## Current Status
- ✅ Python 3.11.13 detected correctly
- ✅ Oryx build completes successfully  
- ✅ All packages installed (gunicorn, flask, etc.)
- ❌ Python app never starts - only .NET Core/Kudu

## Required Azure Portal Settings

### 1. Configuration → General Settings
- **Runtime Stack:** Python 3.11
- **Startup Command:** `gunicorn --bind=0.0.0.0:8000 --workers 1 --timeout 600 --access-logfile - --error-logfile - --log-level info app:APP`

### 2. Configuration → Application Settings
Add these key-value pairs:
- `WEBSITES_PORT` = `8000`
- `PYTHONUNBUFFERED` = `1`
- `SCM_DO_BUILD_DURING_DEPLOYMENT` = `true`

### 3. Expected Startup Logs (missing)
After restart, you should see:
```
[2025-07-27T20:30:00Z] Starting gunicorn 23.0.0
[2025-07-27T20:30:00Z] Listening at: http://0.0.0.0:8000 (1)
[2025-07-27T20:30:00Z] Using worker: sync
[2025-07-27T20:30:00Z] Booting worker with pid: 123
[2025-07-27T20:30:00Z] Flask app created successfully: app
```

## Troubleshooting Steps
1. Verify startup command is saved in Azure Portal (not just locally)
2. Check Application Settings are applied
3. Restart app service completely
4. Monitor logs immediately after restart
5. If still fails, check SSH console: `https://<app-name>.scm.azurewebsites.net`

## File Verification
- ✅ app.py exists with APP variable
- ✅ requirements.txt present
- ✅ Python runtime detected
- ✅ No web.config (removed)