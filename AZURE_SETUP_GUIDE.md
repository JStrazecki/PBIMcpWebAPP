# Azure Setup Guide for Power BI MCP Server

## Overview
This guide covers setting up your Power BI MCP Server on Azure App Service with proper authentication and environment configuration.

## Prerequisites
- ✅ Azure subscription with appropriate permissions
- ✅ Power BI app registration (you already have this)
- ✅ GitHub repository with MCP server code

## 1. Azure App Service Deployment

### Create App Service
```bash
# Login to Azure
az login

# Create resource group (if needed)
az group create --name powerbi-mcp-rg --location "East US"

# Create App Service plan
az appservice plan create \
  --name powerbi-mcp-plan \
  --resource-group powerbi-mcp-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --resource-group powerbi-mcp-rg \
  --plan powerbi-mcp-plan \
  --name pbimcp \
  --runtime "PYTHON|3.11" \
  --deployment-source-url https://github.com/YOUR-USERNAME/YOUR-REPO-NAME
```

### Alternative: Azure Portal Deployment
1. Go to Azure Portal → Create Resource → Web App
2. **Basics**:
   - Subscription: Your subscription
   - Resource Group: Create new `powerbi-mcp-rg`
   - Name: `pbimcp` (or your preferred name)
   - Runtime: Python 3.11
   - Operating System: Linux
   - Region: East US (or preferred)
3. **Deployment**:
   - Enable GitHub Actions: Yes
   - Connect to your GitHub repository
4. Create and wait for deployment

## 2. Environment Variables Configuration

### Required Environment Variables

#### Power BI App Registration (You Already Have These)
```bash
# Your existing Power BI app registration
AZURE_CLIENT_ID=your-existing-client-id
AZURE_CLIENT_SECRET=your-existing-client-secret  
AZURE_TENANT_ID=your-tenant-id
```

#### MCP Server Access Control (New - Choose Your Own)

**What These Are**: These are NOT Azure AD applications or registrations. They are simple username/password-like credentials that YOU create to control who can connect to your MCP server.

**Think of it like**:
- A Wi-Fi password for your network
- A shared secret for your team
- A simple gate-keeper credential

**How It Works**:
1. **You choose** any Client ID you want (like "MyCompany-Claude-Access")
2. **You choose** any secret you want (like a strong password)
3. **You set these** in your Azure Web App environment variables
4. **Your MCP server** checks these credentials when Claude tries to connect
5. **Only people with these credentials** can connect to your MCP server

**Example Scenario**:
- Your company name: "Acme Corp"
- You decide: `MCP_CLIENT_ID = "AcmeCorp-Claude-MCP"`
- You decide: `MCP_CLIENT_SECRET = "SuperSecure2024!Acme"`
- You give these credentials to your authorized Claude users
- Anyone else who finds your URL cannot connect without these credentials

### User Access Management Theory

**Current Setup (What You Have)**:
- ✅ **Power BI App Registration**: Your server uses this to access Power BI workspaces
- ✅ **Azure Web App**: Your MCP server is deployed and running
- ❓ **MCP Access Control**: Missing - anyone with URL can potentially connect

**The Missing Layer - MCP Access Control**:

**Problem Without It**:
- Your MCP server URL might be: `https://pbimcp.azurewebsites.net`
- Anyone who discovers this URL could try to connect via Claude
- Currently, your server would let anyone through

**Solution - Shared Credentials**:
- Add a "front door" authentication layer
- Only people with the right "key" can enter
- After they enter, they get full access to your Power BI data

**Real-World Analogy**:
```
Building Access Control:
├── Building (Power BI) - Secured by Azure AD App Registration ✅
├── Office Floor (Your MCP Server) - Running on Azure Web App ✅  
└── Front Door (MCP Access) - Missing lock! ❌
```

**Two-Layer Security Model**:
1. **Layer 1 - MCP Access**: Who can connect to your server?
2. **Layer 2 - Power BI Access**: What data can the server access? (you already have this)

### Azure Portal Configuration Process

**Step 1: Choose Your Credentials**
- Go to Azure Portal → Your Web App → Configuration → Application Settings
- You'll add 2 new environment variables with values YOU decide

**Step 2: Decide on Naming Convention**
- `MCP_CLIENT_ID`: Could be "CompanyName-Department-Purpose"
  - Examples: "Acme-Finance-Claude", "MyOrg-Analytics-MCP", "Company-PowerBI-Access"
- `MCP_CLIENT_SECRET`: A strong password you create
  - Examples: Complex passwords like "Acme2024!PowerBI$Secure"

**Step 3: Distribution Strategy**
- **Option A - Single Shared Credential**: Everyone uses same Client ID/Secret
  - ✅ Simple to manage
  - ❌ Can't revoke individual users
  - ✅ Good for small teams

- **Option B - Multiple Credentials**: Different credentials for different groups
  - ❌ More complex server code needed
  - ✅ Can revoke specific groups
  - ✅ Better audit trail

**Step 4: User Communication**
When you give credentials to users, they need:
- Server URL: `https://pbimcp.azurewebsites.net`
- Client ID: Your chosen MCP_CLIENT_ID value
- Client Secret: Your chosen MCP_CLIENT_SECRET value
- Instructions: "Use OAuth2 authentication in Claude"

### Set Environment Variables in Azure

#### Method 1: Azure CLI
```bash
# Set Power BI credentials (use your existing values)
az webapp config appsettings set \
  --resource-group powerbi-mcp-rg \
  --name pbimcp \
  --settings \
    AZURE_CLIENT_ID="your-existing-client-id" \
    AZURE_CLIENT_SECRET="your-existing-client-secret" \
    AZURE_TENANT_ID="your-tenant-id" \
    MCP_CLIENT_ID="your-company-mcp-client" \
    MCP_CLIENT_SECRET="your-secure-secret-here"
```

#### Method 2: Azure Portal (Recommended for You)

**Since your app is already deployed and working, use this approach:**

1. **Navigate to Your Web App**:
   - Azure Portal → App Services → [Your App Name]
   - Left sidebar → Settings → Configuration

2. **Review Existing Variables** (you should already have these):
   - `AZURE_CLIENT_ID`: Your existing Power BI app client ID ✅
   - `AZURE_CLIENT_SECRET`: Your existing Power BI app secret ✅
   - `AZURE_TENANT_ID`: Your Azure tenant ID ✅

3. **Add New MCP Control Variables**:
   - Click "+ New application setting"
   - **First Variable**:
     - Name: `MCP_CLIENT_ID`
     - Value: Your chosen access ID (e.g., "AcmeFinance-Claude-PowerBI")
   - **Second Variable**:
     - Name: `MCP_CLIENT_SECRET` 
     - Value: Your chosen strong password (e.g., "Acme2024!PowerBI$TeamAccess")

4. **Save and Restart**:
   - Click "Save" at the top
   - Your app will automatically restart with new variables

**What Happens After This**:
- Your server will start validating MCP connections
- Only users with YOUR chosen credentials can connect
- Your Power BI integration continues working exactly as before
- You control who gets access by sharing (or not sharing) these credentials

**Practical Example**:
```
Company: "Contoso Corp"
Team: "Finance Department" 
Purpose: "Claude PowerBI Access"

You decide:
MCP_CLIENT_ID = "Contoso-Finance-Claude2024"
MCP_CLIENT_SECRET = "ContosoFinance!PowerBI$2024"

You share these with:
- John (Finance Manager)
- Sarah (Financial Analyst) 
- Mike (CFO)

You don't share with:
- Random internet users
- Other departments (until you decide to)
- Former employees (you can change the password)
```

## 3. Power BI App Registration Verification

Since you already have this working, verify these settings:

### Required API Permissions
- `https://analysis.windows.net/powerbi/api/Dataset.Read.All`
- `https://analysis.windows.net/powerbi/api/Workspace.Read.All`
- `https://analysis.windows.net/powerbi/api/Report.Read.All` (optional)

### Authentication Settings
- **Supported account types**: Single tenant or multitenant
- **Redirect URIs**: Not needed for client credentials flow
- **Client secret**: Active and not expired

### Test Your Existing Setup
```bash
# Test Power BI token acquisition (replace with your values)
curl -X POST https://login.microsoftonline.com/YOUR-TENANT-ID/oauth2/v2.0/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=YOUR-CLIENT-ID&client_secret=YOUR-CLIENT-SECRET&scope=https://analysis.windows.net/powerbi/api/.default&grant_type=client_credentials"
```

## 4. Azure App Service Configuration

### Startup Configuration
Create `startup.sh` (should already exist in your repo):
```bash
#!/bin/bash
python -m gunicorn --bind 0.0.0.0:8000 --timeout 120 mcp_simple_server:app
```

### Application Settings in Azure Portal
1. **General Settings**:
   - Python version: 3.11
   - Startup command: `startup.sh`
2. **Path Mappings**: Default (leave empty)
3. **HTTPS Only**: Enabled

## 5. Custom Domain and SSL (Optional)

### Add Custom Domain
```bash
# Add custom domain
az webapp config hostname add \
  --resource-group powerbi-mcp-rg \
  --webapp-name pbimcp \
  --hostname your-domain.com

# Add SSL certificate
az webapp config ssl bind \
  --resource-group powerbi-mcp-rg \
  --name pbimcp \
  --certificate-thumbprint YOUR-CERT-THUMBPRINT \
  --ssl-type SNI
```

## 6. Monitoring and Logs

### Enable Application Insights
```bash
# Create Application Insights
az monitor app-insights component create \
  --app pbimcp-insights \
  --location eastus \
  --resource-group powerbi-mcp-rg \
  --application-type web

# Link to App Service
az webapp config appsettings set \
  --resource-group powerbi-mcp-rg \
  --name pbimcp \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY="your-insights-key"
```

### View Logs
```bash
# Stream logs
az webapp log tail --resource-group powerbi-mcp-rg --name pbimcp

# Download logs
az webapp log download --resource-group powerbi-mcp-rg --name pbimcp
```

## 7. Security Best Practices

### Network Security
- Enable HTTPS only
- Consider adding IP restrictions if needed
- Use managed identity where possible

### Secrets Management
- Store secrets in Azure Key Vault (advanced)
- Rotate client secrets regularly
- Monitor access logs

### Azure Key Vault Integration (Optional Advanced Setup)
```bash
# Create Key Vault
az keyvault create \
  --name pbimcp-vault \
  --resource-group powerbi-mcp-rg \
  --location eastus

# Store secrets
az keyvault secret set --vault-name pbimcp-vault --name "azure-client-secret" --value "your-secret"
az keyvault secret set --vault-name pbimcp-vault --name "mcp-client-secret" --value "your-mcp-secret"

# Grant App Service access
az webapp identity assign --resource-group powerbi-mcp-rg --name pbimcp
az keyvault set-policy --name pbimcp-vault --object-id YOUR-APP-OBJECT-ID --secret-permissions get
```

## 8. Testing Your Deployment

### Health Check
```bash
# Test server health
curl https://pbimcp.azurewebsites.net/health

# Test MCP discovery
curl https://pbimcp.azurewebsites.net/.well-known/mcp

# Test configuration endpoint
curl https://pbimcp.azurewebsites.net/claude-config
```

### Claude.ai Connection Test
1. Go to Claude.ai → Settings → Connectors
2. Add Remote MCP Server:
   - URL: `https://pbimcp.azurewebsites.net`
   - Authentication: OAuth2
   - Client ID: Your `MCP_CLIENT_ID` value
   - Client Secret: Your `MCP_CLIENT_SECRET` value
3. Save and test connection

## 9. Deployment Pipeline (GitHub Actions)

Your deployment should be automated via GitHub Actions. Check `.github/workflows/` for:

```yaml
name: Deploy to Azure
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'pbimcp'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

## 10. Troubleshooting

### Common Issues
1. **500 Internal Server Error**: Check application logs for Python errors
2. **Authentication Failed**: Verify Power BI app registration permissions
3. **Connection Timeout**: Check if app is sleeping (upgrade to higher tier)
4. **CORS Issues**: Verify CORS configuration in Flask app

### Debug Commands
```bash
# Check app status
az webapp show --resource-group powerbi-mcp-rg --name pbimcp --query state

# Restart app
az webapp restart --resource-group powerbi-mcp-rg --name pbimcp

# Check environment variables
az webapp config appsettings list --resource-group powerbi-mcp-rg --name pbimcp
```

## Summary

Your MCP server is now:
- ✅ Deployed on Azure App Service
- ✅ Secured with client credential validation
- ✅ Connected to Power BI with your existing app registration
- ✅ Ready for Claude Enterprise users with proper credentials

**Next Steps**:
1. Set your custom `MCP_CLIENT_ID` and `MCP_CLIENT_SECRET` values
2. Share these credentials with authorized Claude users
3. Monitor usage through Azure Application Insights
4. Consider setting up Azure Key Vault for enhanced security