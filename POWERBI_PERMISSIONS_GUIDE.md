# Power BI Permissions Troubleshooting Guide

## Current Issue
Your MCP server can successfully:
- ✅ Authenticate with Power BI (token generation works)
- ✅ List workspaces
- ✅ List datasets within workspaces
- ❌ Query datasets (fails with MSOLAP connection error)

## Error Details
```
"Failed to open the MSOLAP connection"
"DatasetExecuteQueriesError"
```

## Root Cause
The service principal has **Viewer** access to the workspace but needs **Member** access to query datasets.

## Solution Steps

### 1. Grant Member Access to Service Principal

In Power BI Service:
1. Go to the workspace: **Onetribe Demo**
2. Click on **Manage access** (or the three dots menu → Workspace access)
3. Find your service principal (it will show the Application ID)
4. Change role from **Viewer** to **Member** or **Admin**
5. Save changes

### 2. Enable Service Principal Access in Power BI Admin Portal

Power BI Admin needs to:
1. Go to Power BI Admin Portal → Tenant settings
2. Find **Developer settings** section
3. Enable **Service principals can use Power BI APIs**
4. Add your service principal to the security group (or enable for entire organization)
5. Enable **Service principals can access read-only Power BI admin APIs** if needed

### 3. Dataset-Level Permissions

For each dataset you want to query:
1. Go to the dataset settings
2. Click **Manage permissions**
3. Ensure the service principal has **Build** permission
4. If using Row-Level Security (RLS), assign appropriate roles

### 4. API Permissions in Azure AD

Ensure your App Registration has these API permissions:
- **Power BI Service**
  - Dataset.Read.All (Application)
  - Workspace.Read.All (Application)
  - Optional: Dataset.ReadWrite.All if you need write access

### 5. Verify Credentials

Your environment variables should be set:
```bash
AZURE_CLIENT_ID=<your-app-id>
AZURE_CLIENT_SECRET=<your-secret>
AZURE_TENANT_ID=<your-tenant-id>
```

## Testing After Changes

1. Wait 5-10 minutes for permissions to propagate
2. Try the query again in Claude.ai
3. If still failing, check Azure AD logs for authentication issues

## Common Issues

### Issue: "Dataset was not found"
- Service principal needs workspace Member access
- Dataset might be in a Premium-only workspace

### Issue: "Failed to open MSOLAP connection"
- Service principal needs Member (not Viewer) role
- Dataset security settings might be blocking access

### Issue: Token works but queries fail
- This is exactly your current situation
- Solution: Upgrade from Viewer to Member role

## Contact for Permissions

Based on your workspace configuration:
- **Onetribe Demo**: Contact jakub@onetribeadvisory.com
- **RMC Demo Application**: Contact martin@onetribeadvisory.com

Request them to:
1. Add your service principal as a **Member** of the workspace
2. Grant **Build** permissions on the datasets you need to query

## Alternative: Manual Token

If you have a personal Power BI Pro license, you can temporarily use a manual token:
1. Get a token from https://docs.microsoft.com/en-us/rest/api/power-bi/
2. Set environment variable: `POWERBI_TOKEN=<your-token>`
3. This bypasses service principal authentication

## Verification Commands

After fixing permissions, these should all work:
```
1. List workspaces ✓ (already works)
2. List datasets ✓ (already works) 
3. Query dataset ✓ (should work after Member access)
```