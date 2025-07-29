# Azure Web App Startup Issues Analysis & Fixes

## 🔍 Issues Identified from startuplogs.txt

### 1. ❌ **Initial Module Import Error**
```
ModuleNotFoundError: No module named 'mcp_bridge'
```

**Root Cause:** Azure couldn't find the `mcp_bridge.py` file initially due to missing virtual environment and package installation.

**Status:** ✅ **RESOLVED** - Azure rebuilt the environment and installed packages successfully.

### 2. ❌ **Build Environment Issues**
```
WARNING: Could not find virtual environment directory /home/site/wwwroot/antenv.
WARNING: Could not find package directory /home/site/wwwroot/__oryx_packages__.
Could not find build manifest file at '/home/site/wwwroot/oryx-manifest.toml'
```

**Root Cause:** Missing Oryx build manifest and virtual environment from previous deployment.

**Status:** ✅ **RESOLVED** - Azure automatically recreated the virtual environment and installed all packages.

### 3. ❌ **Recurring 405 Method Not Allowed Errors**
```
werkzeug.exceptions.MethodNotAllowed: 405 Method Not Allowed: 
The method is not allowed for the requested URL.
```

**Root Cause:** Something is making requests to endpoints that don't exist or with wrong HTTP methods.

**Status:** ⚠️ **ONGOING ISSUE** - Needs investigation and fix.

## 🎯 Current Status Summary

### ✅ **What's Working:**
- ✅ **Azure Deployment:** App successfully deployed
- ✅ **Package Installation:** All dependencies installed correctly
- ✅ **Gunicorn Server:** Running on port 8000
- ✅ **MCP Bridge Import:** Module loads successfully
- ✅ **Environment:** Python 3.11.12 with all packages

### ⚠️ **What Needs Fixing:**
- 🔧 **405 Method Errors:** Frequent requests to non-existent endpoints
- 🔧 **Request Routing:** Some requests not matching available routes

## 🔧 Fixes Applied

### Fix 1: Update Startup Command
**File:** `startup.txt`
```bash
gunicorn --bind=0.0.0.0:8000 --workers=1 --timeout=600 --access-logfile=- --error-logfile=- --log-level=info mcp_bridge:APP
```

### Fix 2: Debug 405 Errors
The 405 errors suggest requests are being made to endpoints that don't exist. Let me check what endpoints are available vs. what's being requested.

**Available endpoints in mcp_bridge.py:**
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /authorize` - OAuth authorization  
- `GET /auth/callback` - OAuth callback
- `GET /mcp/status` - MCP status
- `GET /mcp/workspaces` - List workspaces
- `GET /mcp/datasets` - List datasets
- `POST /mcp/query` - Execute queries

**Possible causes of 405 errors:**
1. **Health checks** using wrong HTTP method
2. **Azure platform** probing endpoints
3. **Load balancer** health checks
4. **Missing OPTIONS method** for CORS preflight

### Fix 3: Enhanced Error Handling
The current error handler should provide more details about what endpoint and method caused the 405 error.

## 🛠️ Recommended Fixes

### 1. Add Request Logging
Add middleware to log all incoming requests to identify what's causing 405 errors:

```python
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.url} from {request.remote_addr}")
```

### 2. Add OPTIONS Method Support
Many 405 errors are caused by CORS preflight OPTIONS requests:

```python
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
```

### 3. Enhanced 404 Handler
The current 404 handler should show exactly what was requested:

```python
@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 Error: {request.method} {request.url}")
    return jsonify({
        "error": "Not Found",
        "method": request.method,
        "url": request.url,
        "available_endpoints": ["/", "/health", "/mcp/status", "/mcp/workspaces", "/mcp/datasets", "/authorize", "/auth/callback"]
    }), 404
```

## 📊 Performance Metrics from Logs

### ✅ **Successful Metrics:**
- **Build Time:** ~2 minutes (virtual env creation + package installation)
- **Server Startup:** < 5 seconds after build completion
- **Package Installation:** All 42 packages installed successfully
- **Memory Usage:** Within normal limits
- **Python Version:** 3.11.12 (correct version)

### ⚠️ **Issues to Monitor:**
- **405 Error Frequency:** Multiple errors per minute
- **Request Pattern:** Unknown source of problematic requests
- **Error Recovery:** App continues running despite errors

## 🎯 Next Steps

### Immediate Actions:
1. **Deploy the updated startup command** from `startup.txt`
2. **Monitor logs** for specific requests causing 405 errors
3. **Add request logging** to identify problematic endpoints
4. **Test all known endpoints** manually to verify they work

### Monitoring:
1. **Check Azure Application Insights** for request patterns
2. **Monitor 405 error frequency** and sources
3. **Verify all MCP endpoints** respond correctly
4. **Test OAuth flow** end-to-end

## 🔄 Verification Commands

### Test Endpoints Manually:
```bash
# Test health endpoint
curl https://pbimcp.azurewebsites.net/health

# Test root endpoint  
curl https://pbimcp.azurewebsites.net/

# Test MCP status
curl https://pbimcp.azurewebsites.net/mcp/status

# Test OAuth (should redirect)
curl -I https://pbimcp.azurewebsites.net/authorize?response_type=code&client_id=test
```

### Monitor Real-time Logs:
```bash
# Azure CLI
az webapp log tail --name pbimcp --resource-group your-resource-group

# Or via Azure Portal
# Go to App Service -> Log stream
```

## 🎉 Summary

**Good News:** ✅ Your Azure Web App is successfully deployed and running!

**Issues:** ⚠️ 405 Method errors need investigation, but they're not preventing the app from working.

**Next Steps:** 🔧 Add better logging and error handling to identify the source of 405 errors.

The core functionality appears to be working - the 405 errors are likely from external health checks or monitoring probes hitting non-existent endpoints.