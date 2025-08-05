# Azure App Service Deployment Fix

The deployment is failing because Azure can't find `run_fastmcp.py` in the deployment directory. Here's how to fix it:

## Immediate Actions

### 1. In Azure Portal - App Service Configuration

Go to your App Service → Configuration → General settings:

1. **Stack**: Python
2. **Major version**: Python 3.11
3. **Minor version**: Python 3.11.x
4. **Startup Command**: `python run_fastmcp.py`

### 2. In Azure Portal - Deployment Center

1. Go to Deployment Center
2. If using GitHub:
   - Disconnect and reconnect the repository
   - Ensure it's building from the `main` branch
   - Check "Run build" is enabled

### 3. Force Redeploy via Azure CLI

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "your-subscription-id"

# Restart the app service
az webapp restart --name pbimcp --resource-group your-resource-group

# Force a new deployment
az webapp deployment source sync --name pbimcp --resource-group your-resource-group
```

### 4. Alternative: Use ZIP Deploy

If Git deployment continues to fail:

```bash
# Create a ZIP of your project (excluding .git, __pycache__, etc.)
# From your project root:
zip -r deploy.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc" -x ".env"

# Deploy using Azure CLI
az webapp deployment source config-zip --resource-group your-resource-group --name pbimcp --src deploy.zip
```

## Root Cause

The logs show that Oryx (Azure's build system) is not properly copying files to `/home/site/wwwroot/`. This can happen when:

1. The build cache is corrupted
2. Git deployment has sync issues
3. The deployment configuration is incorrect

## Verification Steps

After redeployment, check:

1. **Kudu Console** (https://pbimcp.scm.azurewebsites.net):
   - Navigate to `/home/site/wwwroot/`
   - Verify `run_fastmcp.py` exists
   - Check file permissions

2. **Log Stream** in Azure Portal:
   - Should show FastMCP server starting
   - Look for "Starting MCP server 'Power BI MCP Server'"

## If Still Failing

1. **Clear Build Cache**:
   ```bash
   az webapp config appsettings set --name pbimcp --resource-group your-resource-group --settings WEBSITE_DISABLE_SCM_SEPARATION=true
   ```

2. **Set Build Variables**:
   ```bash
   az webapp config appsettings set --name pbimcp --resource-group your-resource-group --settings \
     SCM_DO_BUILD_DURING_DEPLOYMENT=true \
     ENABLE_ORYX_BUILD=true \
     PYTHON_VERSION=3.11
   ```

3. **Use Custom Startup Script**:
   - Upload `startup.sh` to App Service
   - Set startup command to: `/home/site/wwwroot/startup.sh`

## Expected Successful Logs

When working correctly, you should see:
```
Found build manifest file at '/home/site/wwwroot/oryx-manifest.toml'
Using packages from virtual environment antenv
Starting FastMCP HTTP server on port 8000
```

## Contact Support

If none of these solutions work, the issue may be with the Azure App Service instance itself. Consider:
1. Creating a new App Service instance
2. Contacting Azure Support with the deployment logs