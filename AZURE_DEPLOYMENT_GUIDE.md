# Azure Web App Deployment Guide

Complete deployment guide for your Power BI MCP Finance Server to Azure Web App.

## 🎯 Deployment Modes

### Mode 1: Simplified (Recommended for Azure)
- ✅ **No database dependencies** - perfect for cloud deployment
- ✅ **Faster startup** - minimal resource requirements
- ✅ **Easy troubleshooting** - fewer moving parts
- 🚀 **File**: `main_simple.py` with `requirements_simple.txt`

### Mode 2: Full Featured (Advanced/Local)
- ✅ **Complete functionality** - conversation tracking, metrics
- ❌ **Database required** - SQLite setup needed
- ❌ **More complex** - additional dependencies
- 🚀 **File**: `pbi_mcp_finance/main.py` with `requirements.txt`

## 🚨 Critical Environment Variables

**Your app will not start without these 4 variables:**

### Power BI Authentication (Choose ONE method)

**Method 1: OAuth2 (Recommended)**
```bash
POWERBI_CLIENT_ID=your-powerbi-app-client-id
POWERBI_CLIENT_SECRET=your-powerbi-app-client-secret  
POWERBI_TENANT_ID=your-azure-tenant-id
```

**Method 2: Manual Token (Alternative)**
```bash
POWERBI_TOKEN=your-manual-bearer-token
```

### Security (Required)
```bash
FLASK_SECRET_KEY=generate-random-32-character-string
```

**Generate Flask secret key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🌐 Optional: Web Authentication Setup

**Only needed if you want a web interface with user login:**

### Create Azure AD App Registration (for web authentication)
1. **Go to**: Azure Portal > Azure Active Directory > App registrations
2. **Click**: "New registration"
3. **Fill out**:
   - **Name**: `PowerBI-MCP-Finance-Server-Web`
   - **Supported account types**: Single tenant
   - **Redirect URI**: Web > `https://your-app.azurewebsites.net/auth/callback`

4. **Get these values**:
   - **Application (client) ID** → `AZURE_CLIENT_ID`
   - **Directory (tenant) ID** → `AZURE_TENANT_ID`

5. **Create Client Secret**:
   - Go to "Certificates & secrets" → "New client secret"
   - Copy the **Value** → `AZURE_CLIENT_SECRET`

6. **Set API Permissions**:
   - Go to "API permissions" → Add `User.Read`, `openid`, `profile`, `email`
   - Click "Grant admin consent"

### Add to Azure Web App
```bash
AUTH_ENABLED=true
AZURE_CLIENT_ID=your-web-auth-client-id
AZURE_CLIENT_SECRET=your-web-auth-client-secret
AZURE_REDIRECT_URI=https://your-app.azurewebsites.net/auth/callback
```

## 🚀 Deployment Options

### Option 1: GitHub Actions (Recommended)
**Automatic deployment on every push to main branch**

1. **Push your changes**:
   ```bash
   git add .
   git commit -m "Deploy to Azure"
   git push origin main
   ```

2. **Monitor deployment**: Check GitHub Actions tab in your repository

3. **Fixed Issues**: 
   - ✅ Artifact storage quota resolved
   - ✅ Direct deployment without artifacts
   - ✅ Simplified dependencies

### Option 2: Azure CLI (Manual)
```bash
# Deploy directly to Azure
az webapp up --name your-app-name --resource-group your-rg --runtime "PYTHON:3.11"
```

### Option 3: Azure Portal (ZIP Upload)
1. Create ZIP file (exclude AzureBotTest, venv, .git)
2. Azure Portal > Your Web App > Development Tools > Advanced Tools
3. Upload and extract ZIP

## 🔧 Azure Web App Configuration

### Step 1: Set Environment Variables
**Go to Azure Portal > Your Web App > Configuration > Application settings**

**Add these 4 critical variables:**

In Azure Portal > Your Web App (`pbimcp`) > Configuration > Application settings, add:

**Web Authentication Variables:**
```
AUTH_ENABLED=true
AZURE_CLIENT_ID=<from-step-4-above>
AZURE_CLIENT_SECRET=<from-step-5-above>
AZURE_TENANT_ID=<from-step-4-above>
AZURE_REDIRECT_URI=https://pbimcp.azurewebsites.net/auth/callback
FLASK_SECRET_KEY=<generate-random-32-chars>
```

**Platform Variables:**
```
SCM_DO_BUILD_DURING_DEPLOYMENT=true
WEBSITES_ENABLE_APP_SERVICE_STORAGE=false
PYTHONPATH=/home/site/wwwroot
```

**Keep your existing Power BI variables unchanged.**

### Step 2: Set Startup Command

In Azure Portal > Your Web App > Configuration > General settings:
- **Startup Command**: `startup.sh`

### Step 3: Deploy Code

**Option A: GitHub Deployment (Recommended)**
1. Azure Portal > Your Web App > Deployment Center
2. Source: GitHub
3. Repository: `PbiMCPFinance`
4. Branch: `feature/oauth-auth`
5. Build provider: App Service build service
6. Save and wait for deployment

**Option B: ZIP Deployment**
```bash
# Create deployment ZIP (exclude unnecessary files)
zip -r deploy.zip . -x "venv/*" "*.git/*" "*.log" "__pycache__/*" "*.pyc" "shared/*"

# Deploy
az webapp deploy --resource-group <your-resource-group> --name pbimcp --src-path deploy.zip
```

### Step 4: Verify Deployment

1. **Health Check**: Visit `https://pbimcp.azurewebsites.net/`
   - Should show: `{"status": "healthy", "service": "Power BI MCP Finance Server"}`

2. **Test Authentication**: Visit `https://pbimcp.azurewebsites.net/auth/login`
   - Should redirect to Microsoft login
   - After login, shows success page

3. **Check Logs**: 
   ```bash
   az webapp log tail --name pbimcp --resource-group <your-resource-group>
   ```

## 🔧 Generate FLASK_SECRET_KEY

Generate a random 32-character secret key:

**Option 1 - Python:**
```python
import secrets
print(secrets.token_hex(16))
```

**Option 2 - Online:** Use any secure random string generator

**Option 3 - PowerShell:**
```powershell
[System.Web.Security.Membership]::GeneratePassword(32, 0)
```

## 🐛 Quick Troubleshooting

**"OAuth not configured" error:**
- Check all `AZURE_*` environment variables are set correctly
- Verify client secret is the **Value** not the ID

**"Invalid redirect URI" error:**
- Ensure redirect URI in Azure AD exactly matches: `https://pbimcp.azurewebsites.net/auth/callback`

**App won't start:**
- Check logs with `az webapp log tail`
- Verify `startup.sh` is executable
- Ensure `PYTHONPATH` is set correctly

**Power BI errors:**
- Your existing Power BI configuration remains unchanged
- Check existing `POWERBI_*` environment variables are still set

## 📞 Support

- **View Logs**: Azure Portal > Your Web App > Log stream
- **Download Logs**: Azure Portal > Your Web App > Advanced Tools > Logs
- **Azure Support**: Submit ticket in Azure Portal if needed

---

## ⚡ Quick Summary

1. **Create new Azure AD app** → Get `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
2. **Add environment variables** to Azure Web App configuration
3. **Deploy code** from `feature/oauth-auth` branch  
4. **Test** at `https://pbimcp.azurewebsites.net/auth/login`

Your Power BI MCP server will be live with Microsoft authentication!