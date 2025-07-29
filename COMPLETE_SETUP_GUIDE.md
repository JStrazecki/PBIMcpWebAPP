# Power BI MCP Server - Complete Setup Guide

## 🎯 Overview

This guide shows you how to set up an enterprise-grade Power BI MCP (Model Context Protocol) server that works with Claude.ai Enterprise through Azure API Management.

## 🏗️ Architecture

```
Claude.ai Enterprise
    ↓ OAuth 2.0 Authentication
Azure API Management (Security Gateway)
    ↓ JWT Validation + Rate Limiting + CORS
Azure Web App (MCP Bridge Server)
    ↓ Client Credentials OAuth
Power BI REST API
    ↓ Direct Access
Your Power BI Workspaces & Datasets
```

## 📋 Prerequisites

### Azure Resources Needed
- Azure subscription with permissions to create resources
- Existing Azure App Registration (you have: `5bdb10bc-bb29-4af9-8cb5-062690e6be15`)
- Azure CLI installed and configured
- Claude.ai Enterprise account

### Required Information
- **Azure Tenant ID:** `your-tenant-id`
- **Client ID:** `5bdb10bc-bb29-4af9-8cb5-062690e6be15` (your existing app registration)
- **Client Secret:** From your app registration
- **Your Power BI Account:** With workspace access

## 🚀 Quick Start (5 Steps)

### Step 1: Deploy Azure API Management
```bash
# Windows
.\deploy_apim.bat

# Linux/Mac  
chmod +x deploy_apim.sh
./deploy_apim.sh
```

**⏱️ Duration:** 15-30 minutes  
**Output:** API Management instance with gateway URL

**What this does:**
- Creates Azure API Management instance
- Sets up resource group `rg-pbi-mcp-enterprise`
- Provides gateway URL for next steps

### Step 2: Configure OAuth 2.0
```bash
# Edit configure_oauth_apim.sh with your values:
TENANT_ID="your-tenant-id"
APIM_NAME="your-apim-name-from-step1"
CLIENT_SECRET="your-client-secret"

# Run configuration
chmod +x configure_oauth_apim.sh
./configure_oauth_apim.sh
```

**What this does:**
- Creates OAuth 2.0 server in API Management
- Configures Entra ID integration
- Sets up secure named values

### Step 3: Create MCP API
```bash
# Edit create_mcp_api.sh with your values:
APIM_NAME="your-apim-name"
BACKEND_URL="https://pbimcp.azurewebsites.net"

# Create API and operations
chmod +x create_mcp_api.sh
./create_mcp_api.sh
```

**What this does:**
- Creates Power BI MCP API in API Management
- Sets up all MCP endpoints (health, status, workspaces, datasets, query)
- Configures OAuth endpoints for Claude.ai

### Step 4: Apply Security Policies
```bash
# Edit apply_policies.sh with your APIM name
APIM_NAME="your-apim-name"

# Apply security policies
chmod +x apply_policies.sh
./apply_policies.sh
```

**What this does:**
- Applies JWT token validation
- Configures CORS for Claude.ai
- Sets up rate limiting (100 req/min)
- Adds security headers and audit logging

### Step 5: Update App Registration
In Azure Portal, add these redirect URIs to your app registration:
1. `https://YOUR-GATEWAY-URL/powerbi-mcp/auth/callback`
2. `https://claude.ai/api/mcp/auth_callback`

## 🧪 Testing Your Setup

### Test 1: Verify API Management
```bash
# Edit test_apim_integration.sh with your values
GATEWAY_URL="https://your-apim-gateway.azure-api.net"
TENANT_ID="your-tenant-id"

# Run tests
chmod +x test_apim_integration.sh
./test_apim_integration.sh
```

**Expected Results:**
- ✅ Health endpoint returns 200
- ✅ Secured endpoints require authentication (401)
- ✅ CORS headers present
- ✅ OAuth URL generated

### Test 2: Manual API Testing
```bash
# Test health endpoint (no auth)
curl https://YOUR-GATEWAY-URL/powerbi-mcp/health

# Test OAuth flow
# Visit: https://YOUR-GATEWAY-URL/powerbi-mcp/authorize?response_type=code&client_id=YOUR-CLIENT-ID&redirect_uri=https://claude.ai/api/mcp/auth_callback&scope=https://analysis.windows.net/powerbi/api/.default
```

## ⚙️ Configure Claude.ai Enterprise

### Option A: Via Claude.ai Interface
1. Go to Claude.ai Enterprise settings
2. Navigate to Integrations
3. Add new MCP server integration
4. Use configuration from `claude_enterprise_config.json`

### Option B: Configuration Values
```json
{
  "name": "Power BI MCP Enterprise",
  "type": "remote_mcp_server", 
  "authentication": {
    "type": "oauth2",
    "authorization_url": "https://YOUR-GATEWAY-URL/powerbi-mcp/authorize",
    "token_url": "https://login.microsoftonline.com/YOUR-TENANT-ID/oauth2/v2.0/token",
    "client_id": "5bdb10bc-bb29-4af9-8cb5-062690e6be15",
    "scopes": ["https://analysis.windows.net/powerbi/api/.default"]
  },
  "base_url": "https://YOUR-GATEWAY-URL/powerbi-mcp"
}
```

## 🔧 Configuration Files Reference

| File | Purpose | When to Use |
|------|---------|-------------|
| `deploy_apim.bat/.sh` | Creates API Management | Step 1 - Infrastructure |
| `configure_oauth_apim.sh` | OAuth setup | Step 2 - Authentication |
| `create_mcp_api.sh` | API creation | Step 3 - API endpoints |
| `apply_policies.sh` | Security policies | Step 4 - Security |
| `mcp_api_policies.xml` | Policy definitions | Referenced by Step 4 |
| `claude_enterprise_config.json` | Claude.ai config | Step 5 - Integration |
| `test_apim_integration.sh` | Testing | Verification |

## 🔍 Troubleshooting

### Common Issues

**Issue 1: API Management deployment fails**
```
Solution: Check Azure subscription limits and permissions
Command: az account show --query "user.name"
```

**Issue 2: OAuth configuration fails**
```
Solution: Verify app registration permissions
Check: Azure Portal → App registrations → API permissions
```

**Issue 3: Claude.ai can't connect**
```
Solution: Verify CORS and redirect URIs
Check: Apply policies script ran successfully
```

**Issue 4: Power BI API calls fail**
```
Solution: Check backend server and credentials
Test: https://pbimcp.azurewebsites.net/health
```

### Debug Commands
```bash
# Check API Management status
az apim show --resource-group rg-pbi-mcp-enterprise --name YOUR-APIM-NAME

# Test backend connectivity
curl https://pbimcp.azurewebsites.net/mcp/status

# Check OAuth server
az apim oauth2-server show --resource-group rg-pbi-mcp-enterprise --service-name YOUR-APIM-NAME --server-id powerbi-oauth-server
```

## 🎯 What Each Component Does

### 1. Azure Web App (`pbimcp.azurewebsites.net`)
- **File:** `mcp_bridge.py`
- **Purpose:** HTTP-to-MCP bridge server
- **Features:** Power BI API integration, OAuth handling, MCP tools

### 2. Azure API Management
- **Purpose:** Enterprise security gateway
- **Features:** JWT validation, rate limiting, CORS, audit logging
- **Benefit:** Enterprise-grade security for Claude.ai integration

### 3. MCP Bridge vs Pure MCP Server
- **`mcp_bridge.py`:** HTTP server for Azure Web Apps (production)
- **`mcp_server.py`:** Pure MCP server for local testing
- **Use:** Bridge for cloud, pure for development

### 4. OAuth Flow
1. Claude.ai → API Management `/authorize`
2. User → Microsoft login
3. Microsoft → API Management `/auth/callback`
4. API Management → Claude.ai callback
5. Claude.ai → Authenticated API calls

## 🔐 Security Features

### Implemented Protections
- ✅ **JWT Token Validation** - Azure AD tokens required
- ✅ **OAuth 2.0 Flow** - Secure authorization
- ✅ **Rate Limiting** - 100 calls/min, 10K/day
- ✅ **CORS Configuration** - Claude.ai domains only
- ✅ **Security Headers** - XSS, CSRF protection
- ✅ **Audit Logging** - Complete request tracking
- ✅ **HTTPS Only** - SSL/TLS encryption

### Production Considerations
- Monitor rate limits via Azure Portal
- Review audit logs regularly
- Update security policies as needed
- Scale API Management tier for higher traffic

## 📊 Monitoring & Analytics

### Available Metrics
- **Request Volume:** Real-time API usage
- **Response Times:** Performance monitoring
- **Error Rates:** Failed request tracking
- **Authentication Events:** OAuth success/failure
- **Rate Limit Hits:** Usage pattern analysis

### Access Analytics
1. Azure Portal → API Management → Analytics
2. View request metrics, top operations, response codes
3. Set up alerts for high error rates or rate limit hits

## 🎉 Success Criteria

Your setup is complete when:
- ✅ All test scripts pass
- ✅ Claude.ai can authenticate via OAuth
- ✅ Power BI workspaces are accessible through Claude.ai
- ✅ API Management shows request analytics
- ✅ Security policies are active

## 💡 Next Steps After Setup

1. **Monitor Usage:** Check API Management analytics
2. **Optimize Performance:** Adjust rate limits as needed
3. **Enhanced Security:** Add IP restrictions if required
4. **Scale Infrastructure:** Upgrade API Management tier for production
5. **User Training:** Educate team on Claude.ai + Power BI capabilities

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Azure Portal logs for API Management
3. Test individual components (backend, OAuth, API calls)
4. Verify all configuration values match your environment

Your enterprise-grade Power BI MCP server is now ready for Claude.ai! 🚀