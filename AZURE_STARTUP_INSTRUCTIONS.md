# Azure Startup Configuration - DIRECT GUNICORN OPTIMIZED

## RECOMMENDED: Use Direct Gunicorn Command

Your app has been optimized for direct gunicorn startup. This bypasses potential startup script issues.

## Step-by-Step Configuration:

### 1. Configure Direct Startup Command in Azure Portal
1. Go to **Azure Portal** → Your Web App `pbimcp` → **Configuration** → **General Settings**
2. In the **Startup Command** field, enter:
   ```bash
   gunicorn --bind 0.0.0.0:8000 --workers 1 --timeout 600 --access-logfile - --error-logfile - --log-level info app:APP
   ```
3. Click **Save**
4. **Restart** your Web App

### 2. Alternative: Use startup.sh (if needed)
If you prefer the startup script approach:
```bash
bash startup.sh
```

### 3. Full MCP Server Restored
Your configuration has been restored to use the **complete MCP server**:

- ✅ `app.py` - **Full FastMCP server** with all Power BI tools
- ✅ `requirements.txt` - **FastMCP included** for complete MCP functionality  
- ✅ `startup.sh` - **FastMCP verification** and `app:APP` startup
- ✅ `Procfile` - **Updated** to use `app:APP`
- ✅ `startupcommand.txt` - **Updated** with direct gunicorn command

## MCP Tools Available:

Your full MCP server now includes these tools:
1. `get_powerbi_status` - Power BI authentication status
2. `health_check` - Complete system health check
3. `list_powerbi_workspaces` - List Power BI workspaces
4. `get_powerbi_datasets` - Get datasets from workspaces
5. `execute_powerbi_query` - Execute DAX/M queries

## Expected Behavior After Fix:

You should see these messages in Azure logs with direct gunicorn startup:
```
FastMCP imported successfully
Flask and CORS imported successfully
FastMCP server initialized successfully
Flask app and CORS initialized successfully
=== Power BI MCP Server Direct Startup ===
Python version: 3.11.*
Working directory: /home/site/wwwroot
Running on Azure: True
Azure hostname: pbimcp.azurewebsites.net
Power BI auth status: {'status': 'not_configured', 'type': 'none'}
Available MCP tools: get_powerbi_status, health_check, list_powerbi_workspaces, get_powerbi_datasets, execute_powerbi_query
Flask app created successfully: app
App routes available: ['/static/<path:filename>', '/', '/health', '/api/powerbi/workspaces']
Power BI MCP Server ready for gunicorn startup
```

## Power BI Configuration:

Set these environment variables in Azure Portal → Configuration → Application Settings:
```
POWERBI_CLIENT_ID=<your-client-id>
POWERBI_CLIENT_SECRET=<your-client-secret>
POWERBI_TENANT_ID=<your-tenant-id>
```

Or use a manual token:
```
POWERBI_TOKEN=<your-bearer-token>
```