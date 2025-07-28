# 🔧 Azure Environment Variables Setup

## 🎯 Using Your Existing App Registration

You already have "Assistant Power BI" app registration with these variables:
- ✅ `POWERBI_CLIENT_ID`
- ✅ `POWERBI_CLIENT_SECRET` 
- ✅ `POWERBI_TENANT_ID`

## 🔄 Required Changes

### Option 1: Rename Existing Variables (Recommended)
Go to **Azure Portal** → **pbimcp** → **Configuration** → **Application Settings**

**Rename these existing variables:**
```
POWERBI_CLIENT_ID → AZURE_CLIENT_ID
POWERBI_CLIENT_SECRET → AZURE_CLIENT_SECRET  
POWERBI_TENANT_ID → AZURE_TENANT_ID
```

**Add this new variable:**
```
REDIRECT_URI = https://pbimcp.azurewebsites.net/auth/callback
```

### Option 2: Add New Variables (Keep Both)
Keep your existing `POWERBI_*` variables and add:
```
AZURE_CLIENT_ID = same-value-as-POWERBI_CLIENT_ID
AZURE_CLIENT_SECRET = same-value-as-POWERBI_CLIENT_SECRET
AZURE_TENANT_ID = same-value-as-POWERBI_TENANT_ID
REDIRECT_URI = https://pbimcp.azurewebsites.net/auth/callback
```

## 📋 Final Environment Variables List

After setup, you should have:
```
AZURE_CLIENT_ID = your-assistant-powerbi-client-id
AZURE_CLIENT_SECRET = your-assistant-powerbi-secret
AZURE_TENANT_ID = your-tenant-id
REDIRECT_URI = https://pbimcp.azurewebsites.net/auth/callback
```

## ✅ Steps to Complete

1. **Azure Portal** → **pbimcp** → **Configuration** → **Application Settings**
2. **Rename or add** the variables above
3. **Click Save**
4. **Restart** the Web App
5. **Test**: Visit `https://pbimcp.azurewebsites.net/auth/url`

## 🔗 Claude.ai MCP Configuration

Use the same values:
```
Server Name: Power BI Finance Server
Remote MCP Server URL: https://pbimcp.azurewebsites.net
OAuth Client ID: your-assistant-powerbi-client-id
OAuth Client Secret: your-assistant-powerbi-secret
```

## 🎉 Done!

Your existing "Assistant Power BI" app registration will now work with OAuth multi-tenant authentication through Claude.ai!