# API Management Scripts Directory

## 📁 Script Organization

### 🚀 **Fully Automated Scripts (No Manual Configuration)**
These scripts automatically pull configuration from your Azure Web App environment variables:

- `deploy_complete_automation.sh` - **RECOMMENDED**: One-command deployment
- `configure_oauth_from_webapp.sh` - OAuth setup using Web App env vars
- `test_integration.sh` - Automated testing with discovered configuration

### ⚙️ **Manual Configuration Scripts (0 suffix)**
These scripts require you to edit values before running:

- `deploy_apim0.sh` - Basic API Management deployment (edit resource names)
- `configure_oauth0.sh` - OAuth setup with manual values
- `create_api0.sh` - API creation with manual backend URL
- `apply_policies0.sh` - Security policies with manual APIM name
- `test_integration0.sh` - Testing with manual gateway URL

## 🎯 **Recommended Usage**

### Option 1: Fully Automated (Recommended) ⚡
```bash
# 1. Set Web App environment variables (one time)
az webapp config appsettings set --name "pbimcp" --resource-group "your-webapp-rg" \
  --settings AZURE_TENANT_ID="your-tenant-id" \
             AZURE_CLIENT_ID="your-client-id" \
             AZURE_CLIENT_SECRET="your-client-secret"

# 2. Run complete automation
cd api-management
chmod +x deploy_complete_automation.sh
./deploy_complete_automation.sh
```

### Option 2: Step-by-Step Automated
```bash
cd api-management

# Step 1: Deploy API Management
chmod +x deploy_apim0.sh
# Edit deploy_apim0.sh if needed, then run:
./deploy_apim0.sh

# Step 2: Configure OAuth (from Web App)
chmod +x configure_oauth_from_webapp.sh
./configure_oauth_from_webapp.sh

# Step 3: Create API
chmod +x create_api0.sh  
# Edit create_api0.sh for APIM name, then run:
./create_api0.sh

# Step 4: Apply security policies
chmod +x apply_policies0.sh
# Edit apply_policies0.sh for APIM name, then run:
./apply_policies0.sh

# Step 5: Test integration
chmod +x test_integration.sh
./test_integration.sh
```

### Option 3: Fully Manual Configuration
Use all the "0" suffix scripts and edit each one with your specific values.

## 📋 **Required Environment Variables**

Your Azure Web App must have these set:
- `AZURE_TENANT_ID` - Your Azure tenant ID
- `AZURE_CLIENT_ID` - Your app registration client ID  
- `AZURE_CLIENT_SECRET` - Your app registration client secret

## 🔍 **Script Naming Convention**

- **No suffix**: Fully automated, pulls from environment variables
- **0 suffix**: Requires manual editing before running

## 📄 **Generated Files**

After successful deployment:
- `claude_enterprise_config.json` - Configuration for Claude.ai Enterprise
- `deployment_report.md` - Complete deployment summary
- `oauth_configuration.json` - OAuth configuration details

## 🆘 **Troubleshooting**

1. **"Environment variables not found"** - Set them in your Web App first
2. **"APIM name not found"** - Edit the "0" suffix scripts with correct names
3. **"Permission denied"** - Run `chmod +x scriptname.sh` first

## 🎉 **Success Criteria**

Your setup is complete when:
- ✅ API Management is deployed and accessible
- ✅ OAuth flow works with Microsoft authentication  
- ✅ All API endpoints return expected responses
- ✅ Claude.ai can authenticate and access Power BI data