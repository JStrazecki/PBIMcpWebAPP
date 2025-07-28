# Azure Startup Configuration Instructions

## CRITICAL: startupcommand.txt is NOT used by Azure

Azure Web App **IGNORES** the `startupcommand.txt` file. You must configure the startup command through the Azure Portal.

## Step-by-Step Fix:

### 1. Configure Startup Command in Azure Portal
1. Go to **Azure Portal** → Your Web App `pbimcp` → **Configuration** → **General Settings**
2. In the **Startup Command** field, enter:
   ```bash
   bash startup.sh
   ```
3. Click **Save**
4. **Restart** your Web App

### 2. Alternative: Use Procfile (Updated)
Your `Procfile` has been updated to:
```
web: gunicorn --bind=0.0.0.0:8000 --workers 1 --timeout 600 --access-logfile - --error-logfile - --log-level info app_simple:APP
```

### 3. Verify Configuration Files
- ✅ `startup.sh` - Fixed to use `app_simple:APP`
- ✅ `Procfile` - Updated to use `app_simple:APP`  
- ✅ `app_simple.py` - Simplified Flask app (no FastMCP conflicts)
- ✅ `requirements.txt` - Simplified dependencies

## What Was Wrong:

1. **`startupcommand.txt` ignored** - Azure doesn't use this file
2. **Azure defaulted to .NET mode** - Because no valid Python startup command found
3. **No Python app traces in logs** - Because startup.sh never executed

## Expected Behavior After Fix:

You should see these messages in Azure logs:
```
=== PBI MCP Bot Startup ===
Time: [timestamp]
Directory: /home/site/wwwroot
Python: /opt/python/3.11.*/bin/python3
✓ flask installed
✓ msal installed
✓ requests installed
✓ gunicorn installed
✓ PBI MCP app loads successfully
Starting PBI MCP Bot on port 8000...
```

## Backup Options:

If startup.sh still doesn't work, try setting this as Azure startup command:
```bash
cd /home/site/wwwroot && python3 -m gunicorn --bind=0.0.0.0:8000 --workers 1 --timeout 600 app_simple:APP
```