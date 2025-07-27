# Azure Web App Deployment Guide

Simple deployment guide for your Power BI MCP Finance Server to Azure Web App.

## 🤔 Why Create a Separate Azure AD App Registration?

You need to create a **separate** Azure AD app registration (`PowerBI-MCP-Finance-Server`) because:

1. **Different Authentication Flow**: Your existing Power BI registration uses **Service Principal** flow (client credentials) for API access, while the web app needs **OAuth2 Authorization Code** flow for user authentication

2. **Different Redirect URLs**: Web authentication requires specific redirect URLs (`/auth/callback`) that shouldn't be mixed with your existing Power BI service configuration

3. **Different Permissions**: The web app needs user authentication permissions (`User.Read`, `openid`, `profile`) while Power BI needs API access permissions

4. **Security Isolation**: Separating concerns keeps your existing Power BI setup unchanged and secure

**Your existing Power BI variables remain the same** - this new registration is only for web user authentication.

## 📋 What You Need

### Azure AD App Registration (New - for Web Authentication)
1. **Go to**: Azure Portal > Azure Active Directory > App registrations
2. **Click**: "New registration"
3. **Fill out**:
   - **Name**: `PowerBI-MCP-Finance-Server`
   - **Supported account types**: Single tenant
   - **Redirect URI**: Web > `https://pbimcp.azurewebsites.net/auth/callback`

4. **After creation, get these values**:
   - **Application (client) ID** → This becomes `AZURE_CLIENT_ID`
   - **Directory (tenant) ID** → This becomes `AZURE_TENANT_ID`

5. **Create Client Secret**:
   - Go to "Certificates & secrets"
   - Click "New client secret"
   - Copy the **Value** (not the ID!) → This becomes `AZURE_CLIENT_SECRET`

6. **Set API Permissions**:
   - Go to "API permissions"
   - Add these Microsoft Graph permissions:
     - `User.Read` (Delegated)
     - `openid` (Delegated) 
     - `profile` (Delegated)
     - `email` (Delegated)
   - Click "Grant admin consent"

## 🚀 Deployment Steps

### Step 1: Configure Azure Web App Environment Variables

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