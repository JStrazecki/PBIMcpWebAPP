# ☁️ Azure Deployment Files

This directory contains files specifically for Azure Web App deployment and configuration.

## 📁 Files

### Startup Configuration
- `startup.sh` - Azure Web App startup script (comprehensive setup with package verification)
- `../startup.txt` - Simple startup command for Azure (in root directory, used by Azure)

### Server Configuration
- `gunicorn.conf.py` - Gunicorn WSGI server configuration for production

## 🚀 Usage

### Azure Web App Deployment
These files are automatically used by Azure when you deploy your Web App:

1. **Startup Command**: Azure uses `startup.txt` (in root) for the startup command
2. **Startup Script**: If needed, `startup.sh` provides more comprehensive startup logic
3. **Gunicorn Config**: `gunicorn.conf.py` configures the WSGI server

### Manual Configuration
If you need to update the Azure startup process:

```bash
# Update startup command in Azure Portal
# App Service → Configuration → General Settings → Startup Command
# Use content from startup.txt

# Or use the comprehensive startup script
# Set startup command to: ./azure-deployment/startup.sh
```

## ⚙️ Configuration Details

### startup.sh Features:
- ✅ Python environment verification
- ✅ Package installation and verification  
- ✅ Directory setup
- ✅ Application import testing
- ✅ Comprehensive logging

### gunicorn.conf.py Features:
- ✅ Production-ready worker configuration
- ✅ Logging setup
- ✅ Timeout and resource management
- ✅ Azure optimization

## 🎯 Purpose

These files are for:
- ✅ Azure Web App production deployment
- ✅ WSGI server configuration
- ✅ Startup process automation
- ❌ NOT for local development (use local-development/ for that)

## 🔗 Related Files

- `../startup.txt` - Simple startup command (used by Azure)
- `../mcp_bridge.py` - Main application file
- `../requirements.txt` - Python dependencies