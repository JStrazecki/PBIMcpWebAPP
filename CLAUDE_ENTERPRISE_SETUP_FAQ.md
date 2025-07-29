# Claude.ai Enterprise Setup - Frequently Asked Questions

## 1. 📄 Where do I put the Claude Enterprise config?

### ❌ **DO NOT** publish `claude_enterprise_config.json` to Azure Web App

The `claude_enterprise_config.json` file is **NOT** deployed to your Azure Web App. It's a configuration file for Claude.ai Enterprise administrators.

### ✅ **Correct Usage:**

#### Option A: Claude.ai Enterprise Admin Portal (Recommended)
1. **Login** to Claude.ai Enterprise as an administrator
2. **Navigate** to Settings → Integrations → MCP Servers
3. **Click** "Add New Integration"
4. **Use the values** from `claude_enterprise_config.json` to fill out the form:
   ```
   Name: Power BI MCP Enterprise
   Type: Remote MCP Server
   Base URL: https://YOUR-API-MANAGEMENT-GATEWAY/powerbi-mcp
   Authorization URL: https://YOUR-API-MANAGEMENT-GATEWAY/powerbi-mcp/authorize
   Token URL: https://login.microsoftonline.com/YOUR-TENANT-ID/oauth2/v2.0/token
   Client ID: 5bdb10bc-bb29-4af9-8cb5-062690e6be15
   Scopes: https://analysis.windows.net/powerbi/api/.default
   ```

#### Option B: Claude Desktop (Local Development)
For local testing with Claude Desktop, copy the config to:
```
Windows: %APPDATA%\Claude\claude_desktop_config.json
Mac: ~/Library/Application Support/Claude/claude_desktop_config.json
Linux: ~/.config/Claude/claude_desktop_config.json
```

### 📁 **File Locations Summary:**
```
Azure Web App (pbimcp.azurewebsites.net):
├── mcp_bridge.py          ✅ Deploy this
├── requirements.txt       ✅ Deploy this  
├── startup.sh            ✅ Deploy this
└── pbi_mcp_finance/      ✅ Deploy this

Your Local Machine:
├── claude_enterprise_config.json  ❌ Keep local, use for reference
├── deploy_apim.sh               ❌ Keep local, run from here
└── test_apim_integration.sh     ❌ Keep local, run from here

Claude.ai Enterprise Portal:
└── Integration Configuration    ✅ Enter values manually
```

## 2. 🔧 How to set up the API - Will it be automatic?

### ❌ **NO** - The API Management setup is **NOT** automatic

Your Azure Web App (`pbimcp.azurewebsites.net`) is just the **backend server**. The API Management layer requires **separate manual setup**.

### 🏗️ **Two-Layer Architecture:**

```
Layer 1: Azure Web App (Already Deployed) ✅
├── Your current server: https://pbimcp.azurewebsites.net
├── Status: Working (as shown in your info.txt)
└── Purpose: Provides HTTP endpoints for Power BI data

Layer 2: Azure API Management (Needs Manual Setup) ❌
├── New resource: https://YOUR-APIM-GATEWAY.azure-api.net  
├── Status: Not deployed yet
└── Purpose: Enterprise security, OAuth, rate limiting for Claude.ai
```

### 📋 **Required Setup Steps:**

#### Step 1: Deploy API Management (Manual)
```bash
# Run this on your local machine, not on Azure Web App
.\deploy_apim.bat
```
**Duration:** 15-30 minutes  
**Result:** Creates new Azure resource group and API Management instance

#### Step 2: Configure OAuth (Manual)
```bash
# Edit script with your tenant ID first
./configure_oauth_apim.sh
```
**Result:** Sets up OAuth 2.0 server in API Management

#### Step 3: Create API Proxy (Manual)
```bash
# Creates API that forwards to your existing web app
./create_mcp_api.sh
```
**Result:** API Management now proxies calls to `pbimcp.azurewebsites.net`

#### Step 4: Apply Security (Manual)
```bash
# Applies JWT validation, CORS, rate limiting
./apply_policies.sh
```
**Result:** Enterprise security policies active

### 🔄 **What Happens After Setup:**

#### Before API Management:
```
Claude.ai Enterprise → https://pbimcp.azurewebsites.net (DIRECT)
❌ Result: "Error connecting to PowerBIMCP" (Protocol mismatch)
```

#### After API Management:
```
Claude.ai Enterprise → API Management Gateway → pbimcp.azurewebsites.net
✅ Result: Secure OAuth flow, proper MCP integration
```

## 3. 🎯 **Current Status & Next Steps**

### ✅ **What's Already Working:**
- Your Azure Web App is deployed and functional
- Power BI authentication works (client credentials)  
- All MCP endpoints return data correctly
- Backend integration is complete

### 🔧 **What Still Needs Setup:**
- Azure API Management deployment
- OAuth 2.0 server configuration
- Security policies application
- Claude.ai Enterprise integration configuration

### 📝 **Action Items:**

#### For You (Azure Setup):
1. **Run deployment scripts** (from your local machine)
2. **Configure API Management** with your tenant details
3. **Update app registration** redirect URIs
4. **Test the integration** using provided scripts

#### For Claude.ai Enterprise Admin:
1. **Access enterprise admin portal**
2. **Add MCP integration** using values from config file
3. **Test OAuth flow** with your Microsoft account
4. **Verify Power BI access** through Claude.ai

## 4. 🔐 **Security & Access**

### Azure Resources You'll Have:
```
Resource Group: rg-pbi-mcp-enterprise
├── API Management: pbi-mcp-apim-xxxxx
├── Existing Web App: pbimcp.azurewebsites.net
└── Your App Registration: 5bdb10bc-bb29-4af9-8cb5-062690e6be15
```

### Claude.ai Enterprise Access:
- **Admin Setup:** Enterprise administrator configures integration
- **User Access:** All enterprise users can then use Power BI through Claude.ai
- **OAuth Flow:** Each user authenticates with their Microsoft account
- **Permissions:** Users see only Power BI data they have access to

## 5. 🆘 **Common Misunderstandings**

### ❓ "Should I deploy the config file to Azure?"
**❌ NO** - The config file is for Claude.ai Enterprise portal configuration, not Azure deployment.

### ❓ "Will Claude.ai automatically find my Azure Web App?"
**❌ NO** - You need API Management as the intermediary layer for proper protocol handling.

### ❓ "Is my Azure Web App broken?"
**❌ NO** - Your web app is working perfectly. The issue is protocol mismatch without API Management.

### ❓ "Can I skip API Management?"
**❌ NO** - Claude.ai Enterprise requires proper OAuth flow and security that only API Management provides.

## 6. 📞 **Support Matrix**

| Issue | Where to Get Help |
|-------|-------------------|
| Azure Web App problems | Check Azure Portal logs |
| API Management deployment | Use deployment scripts + Azure docs |
| Claude.ai integration | Claude.ai Enterprise support |
| OAuth/permissions | Azure AD documentation |
| Power BI API issues | Microsoft Power BI support |

## 🎉 **Summary**

1. **Your Azure Web App** is complete and working ✅
2. **API Management** needs manual deployment ⏳
3. **Claude config** goes in Enterprise portal, not Azure ✅
4. **OAuth setup** requires additional configuration steps ⏳
5. **End result** will be secure, enterprise-grade integration 🎯

**Next Step:** Run `.\deploy_apim.bat` to start the API Management setup process!