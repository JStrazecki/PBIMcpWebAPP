# Power BI MCP Server Setup Guide

This guide will help you properly configure your Power BI MCP server to resolve authentication and permission issues.

## Current Issues Identified

Based on your logs, you're experiencing two main issues:

1. **"API is not accessible for application" (403 error)** - Missing Dataset.Read.All permission
2. **"Failed to open the MSOLAP connection" (400 error)** - XMLA endpoint access issue

## Step-by-Step Resolution

### 1. Azure AD App Registration Permissions

Your service principal needs the correct API permissions:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Find your app registration (the one with your POWERBI_CLIENT_ID)
4. Click on **API permissions** in the left menu
5. Click **Add a permission**
6. Select **Power BI Service**
7. Choose **Application permissions** (NOT Delegated permissions)
8. Select the following permissions:
   - `Dataset.Read.All` - Required for listing and accessing datasets
   - `Workspace.Read.All` - For listing workspaces (you already have this)
9. Click **Add permissions**
10. **IMPORTANT**: Click **Grant admin consent** button and confirm

### 2. Power BI Admin Portal Settings

Enable service principals to use Power BI APIs:

1. Go to [Power BI Admin Portal](https://app.powerbi.com/admin-portal)
2. Navigate to **Tenant settings**
3. Find **Developer settings** section
4. Locate **Service principals can use Power BI APIs**
5. Enable this setting
6. Choose one of:
   - **The entire organization** (easiest)
   - **Specific security groups** (add a security group containing your service principal)
7. Apply the changes

### 3. Workspace Access Configuration

Add your service principal to workspaces:

1. Go to [Power BI Service](https://app.powerbi.com)
2. Navigate to your workspace (e.g., "Onetribe Demo")
3. Click the **Access** button (or ⋯ menu > Manage access)
4. Click **Add people or groups**
5. Search for your service principal by:
   - Using the Application ID (Client ID)
   - Or the display name of your app registration
6. Select **Member** role (NOT Viewer or Contributor)
7. Click **Add**

### 4. Enable XMLA Endpoint (For DAX Queries)

This requires Premium/PPU workspace:

1. In your Power BI workspace, click ⋯ menu > **Workspace settings**
2. Go to **Premium** tab
3. Under **XMLA Endpoint**, select **Read** or **Read Write**
4. Save changes

**Note**: If you don't see Premium settings, ensure:
- The workspace is assigned to Premium capacity or PPU
- You have admin rights on the workspace

### 5. Dataset-Specific Settings

For each dataset you want to query:

1. Go to dataset settings (⋯ menu on dataset > Settings)
2. Expand **Security** section
3. Ensure **Row-level security (RLS)** isn't blocking the service principal
4. If using RLS, add the service principal to appropriate security roles

## Testing Your Configuration

Run the diagnostic script:

```bash
python diagnose_powerbi_auth.py
```

This will verify:
- Environment variables are set correctly
- Token acquisition works
- API permissions are configured
- Workspace and dataset access

## Environment Variables Required

Ensure these are set in your deployment:

```bash
# Azure AD App Registration
POWERBI_CLIENT_ID=your-client-id
POWERBI_CLIENT_SECRET=your-client-secret
POWERBI_TENANT_ID=your-tenant-id

# Optional: Default workspace configuration
POWERBI_WORKSPACE=Onetribe Demo
POWERBI_WORKSPACE_ID=6d40d0dc-7eb0-44a1-9979-0de51f73c71c
POWERBI_DATASET=Onetribe Demo - Model Finance
```

## Common Issues and Solutions

### Issue: "API is not accessible for application"
**Solution**: Add Dataset.Read.All permission and grant admin consent

### Issue: "Failed to open the MSOLAP connection"
**Solution**: 
- Add service principal as Member to workspace
- Enable XMLA endpoint in workspace settings
- Ensure dataset is in Premium/PPU workspace

### Issue: Works locally but not in Azure
**Solution**: 
- Verify environment variables are set in Azure App Service
- Check if Azure firewall is blocking Power BI API calls
- Ensure managed identity (if used) has correct permissions

## Verification Checklist

- [ ] Dataset.Read.All permission added in Azure AD
- [ ] Admin consent granted for permissions
- [ ] Service principals can use Power BI APIs enabled
- [ ] Service principal added as Member to workspaces
- [ ] XMLA endpoint enabled (for DAX queries)
- [ ] Environment variables configured correctly
- [ ] Diagnostic script shows all green checkmarks

## Need Help?

If you continue to experience issues after following this guide:

1. Run `python diagnose_powerbi_auth.py` and share the output
2. Check Azure AD audit logs for permission errors
3. Verify in Power BI Admin Portal that settings are applied
4. Ensure your Power BI workspace is Premium/PPU if using DAX queries