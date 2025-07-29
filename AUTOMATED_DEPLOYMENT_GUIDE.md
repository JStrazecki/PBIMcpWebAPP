# 🚀 Automated API Management Deployment Guide

## ✨ One-Command Setup

Instead of running 4+ separate scripts manually, you can now deploy everything with **ONE COMMAND**!

### 📋 What Gets Automated

✅ **Resource Group Creation**  
✅ **API Management Deployment** (15-30 minutes)  
✅ **OAuth 2.0 Server Configuration**  
✅ **API Creation & All Endpoints**  
✅ **Security Policies** (JWT, CORS, Rate Limiting)  
✅ **Product Configuration**  
✅ **Endpoint Testing**  
✅ **Configuration File Generation**  

## 🎯 Single Command Usage

### Windows (PowerShell)
```powershell
.\deploy_complete_automation.ps1 -TenantId "your-tenant-id" -ClientId "your-client-id" -ClientSecret "your-client-secret"
```

### Linux/Mac (Bash)
```bash
chmod +x deploy_complete_automation.sh
./deploy_complete_automation.sh "your-tenant-id" "your-client-id" "your-client-secret"
```

## 📝 Required Information

You need these 3 values from your Azure App Registration:

1. **Tenant ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
2. **Client ID**: `5bdb10bc-bb29-4af9-8cb5-062690e6be15` (your existing app)
3. **Client Secret**: `your-secret-value`

### 🔍 Where to Find These Values

**Azure Portal** → **App Registrations** → **Your App** → **Overview**:
- Tenant ID: "Directory (tenant) ID"
- Client ID: "Application (client) ID"

**Client Secret**: **Certificates & secrets** → **Client secrets**

## ⚙️ Optional Parameters

You can customize the deployment:

### PowerShell
```powershell
.\deploy_complete_automation.ps1 `
    -TenantId "your-tenant-id" `
    -ClientId "your-client-id" `
    -ClientSecret "your-client-secret" `
    -ResourceGroupName "my-custom-rg" `
    -ApimName "my-apim-instance" `
    -Location "West US" `
    -WebAppUrl "https://mycustomapp.azurewebsites.net"
```

### Bash
```bash
./deploy_complete_automation.sh \
    "your-tenant-id" \
    "your-client-id" \
    "your-client-secret" \
    "my-custom-rg" \
    "my-apim-instance" \
    "West US" \
    "https://mycustomapp.azurewebsites.net"
```

## ⏱️ Deployment Timeline

| Step | Duration | Description |
|------|----------|-------------|
| 1-2 | 30 seconds | Resource group + validation |
| 3 | **15-30 minutes** | API Management deployment |
| 4-8 | 2-3 minutes | Configuration + testing |
| **Total** | **18-35 minutes** | Complete automated setup |

## 📄 Generated Files

After successful deployment, you'll get:

### `claude_enterprise_config_automated.json`
Ready-to-use configuration for Claude.ai Enterprise portal

### `DEPLOYMENT_SUCCESS_REPORT.md`
Complete deployment summary with:
- All URLs and endpoints
- Configuration values for Claude.ai
- Testing commands
- Monitoring information

## 🎯 Next Steps After Deployment

1. **Claude.ai Enterprise Configuration**:
   - Open Claude.ai Enterprise Admin Portal
   - Add MCP integration using values from the generated report

2. **Test Your Integration**:
   ```bash
   # Health check (should work immediately)
   curl https://your-apim-gateway.azure-api.net/powerbi-mcp/health
   
   # Authenticated endpoint (needs token)
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        https://your-apim-gateway.azure-api.net/powerbi-mcp/mcp/status
   ```

## 🆚 Before vs. After

### ❌ **Manual Process (OLD)**
```bash
# 4 separate scripts to run manually
./deploy_apim.bat                  # 30 minutes
./configure_oauth_apim.sh          # 5 minutes  
./create_mcp_api.sh               # 3 minutes
./apply_policies.sh               # 2 minutes
# Total: 40+ minutes + manual steps
```

### ✅ **Automated Process (NEW)**
```bash
# Single command handles everything
./deploy_complete_automation.sh "tenant" "client" "secret"
# Total: 18-35 minutes, fully automated
```

## 🛠️ Troubleshooting

### Common Issues:

**"Azure CLI not found"**
```bash
# Install Azure CLI first
# Windows: https://aka.ms/installazurecliwindows
# Mac: brew install azure-cli
# Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

**"Login required"**
```bash
az login
# Follow browser authentication
```

**"Permission denied"**
```bash
# Make script executable (Linux/Mac)
chmod +x deploy_complete_automation.sh
```

**"Resource already exists"**
- The script handles existing resources gracefully
- Existing resources are reused, not recreated

## 🎉 Success Indicators

You'll know it worked when you see:
```
🎉 DEPLOYMENT COMPLETE!
================================================
📄 Configuration saved to: claude_enterprise_config_automated.json
📄 Deployment report saved to: DEPLOYMENT_SUCCESS_REPORT.md
🌐 API Gateway URL: https://your-gateway.azure-api.net/powerbi-mcp

Next: Configure Claude.ai Enterprise with the generated configuration!
```

## 📞 Support

If deployment fails:
1. Check the error message
2. Verify your Azure credentials
3. Ensure you have Azure subscription permissions
4. Try running individual steps manually for debugging

**Your API Management setup is now fully automated! 🚀**