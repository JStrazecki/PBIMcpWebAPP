# Repository Cleanup Plan

## Files to Keep (Core Functionality)

### 🎯 **Current Working Solution**
- `mcp_bridge.py` - ✅ Main HTTP-to-MCP bridge server (currently working)
- `mcp_server.py` - ✅ Pure MCP server for local testing
- `requirements.txt` - ✅ Dependencies
- `runtime.txt` - ✅ Python version for Azure
- `gunicorn.conf.py` - ✅ Gunicorn configuration
- `startup.sh` - ✅ Azure startup script
- `Procfile` - ✅ Heroku/Azure process file

### 🏗️ **Azure API Management (Enterprise Solution)**
- `deploy_apim.bat` - ✅ Windows deployment script
- `deploy_apim.sh` - ✅ Linux deployment script  
- `configure_oauth_apim.sh` - ✅ OAuth configuration
- `create_mcp_api.sh` - ✅ API creation script
- `apply_policies.sh` - ✅ Security policy application
- `mcp_api_policies.xml` - ✅ Security policies
- `test_apim_integration.sh` - ✅ Integration testing

### 📋 **Configuration Files**
- `claude_enterprise_config.json` - ✅ Claude.ai Enterprise config
- `claude_desktop_config.json` - ✅ Claude Desktop config
- `setup_local_mcp.bat` - ✅ Local testing setup

### 📚 **Essential Documentation**
- `README.md` - ✅ Main project readme
- `APIM_DEPLOYMENT_COMPLETE.md` - ✅ Complete enterprise guide
- `AZURE_CLAUDE_MCP_ENTERPRISE_GUIDE.md` - ✅ Enterprise setup guide

### 🔧 **Supporting Infrastructure**
- `.deployment` - ✅ Azure deployment config
- `pbi_mcp_finance/` - ✅ Core business logic package

## Files to Remove (Outdated/Duplicate)

### ❌ **Outdated Documentation**
- `AZURE_COMMAND_FIX.md` - Outdated troubleshooting
- `AZURE_DEPLOYMENT_GUIDE.md` - Superseded by APIM guide
- `AZURE_ENV_SETUP.md` - Basic setup, now obsolete
- `AZURE_LINUX_TROUBLESHOOTING.md` - Old troubleshooting
- `AZURE_STARTUP_INSTRUCTIONS.md` - Outdated instructions
- `CUSTOM_MCP_WEBSITE_GUIDE.md` - Not relevant
- `DEBUG_STARTUP.md` - Old debugging info
- `DEPLOYMENT_CHECKLIST.md` - Outdated checklist
- `DEPLOYMENT_COMPARISON.md` - No longer relevant
- `ENVIRONMENT_SETUP.md` - Basic setup, superseded
- `FLASK_SECRET_KEY_GUIDE.md` - Specific issue, resolved
- `SIMPLIFICATION_CHANGES.md` - Development notes
- `STARTUP_DIAGNOSIS.md` - Old debugging
- `startupissue.md` - Old issue tracking

### ❌ **Outdated/Unused Scripts**
- `app.py` - Old Flask app, replaced by mcp_bridge.py
- `app_simple.py` - Simplified version, not needed
- `main_simple.py` - Simplified version, not needed
- `deploy_simple.py` - Simple deployment, superseded
- `run.sh` - Old run script
- `startup example.sh` - Example file
- `test_env.py` - Old testing
- `test_env_simple.py` - Simple testing
- `test_import.py` - Basic import test
- `test_startup.py` - Old startup test

### ❌ **Log/Debug Files**
- `info.txt` - Debug information, temporary
- `startup.txt` - Old startup command
- `startupcommand.txt` - Duplicate startup command
- `Startuplog.txt` - Old log file

### ❌ **Duplicate/Example Files**
- `claude_mcp_config.json` - Superseded by enterprise config
- `example/` - Example files, not needed for production
- `Procfile` - if using startup.sh

## Cleanup Actions

1. **Remove outdated files** - 25+ files to delete
2. **Keep core functionality** - 15 essential files  
3. **Consolidate documentation** - Create single comprehensive guide
4. **Update README.md** - Point to new documentation structure