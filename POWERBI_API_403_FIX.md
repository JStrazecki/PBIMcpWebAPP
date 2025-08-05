# Power BI API 403 Error Fix

## Current Error
```
"API is not accessible for application"
```

This error occurs when trying to access Power BI API endpoints, even though the token is acquired successfully.

## Root Cause
The Azure AD App Registration is missing the required Power BI Service API permissions or they haven't been admin consented.

## Solution

### Step 1: Add API Permissions in Azure Portal

1. Go to Azure Portal → Azure Active Directory → App registrations
2. Find your app registration (using the CLIENT_ID)
3. Click on "API permissions" in the left menu
4. Click "Add a permission"
5. Select "Power BI Service"
6. Choose "Application permissions" (NOT Delegated permissions)
7. Select these permissions:
   - `Tenant.Read.All`
   - `Dataset.Read.All` 
   - `Workspace.Read.All`
   - `Dataflow.Read.All` (optional)
   - `Report.Read.All` (optional)
8. Click "Add permissions"

### Step 2: Grant Admin Consent

**CRITICAL**: After adding permissions, you MUST grant admin consent:
1. In the API permissions page
2. Click "Grant admin consent for [Your Organization]"
3. Confirm the consent
4. Wait for the status to show "Granted for [Your Organization]"

### Step 3: Enable Service Principal in Power BI Admin Portal

This must be done by a Power BI Admin:
1. Go to Power BI Service (app.powerbi.com)
2. Click Settings (gear icon) → Admin portal
3. Go to "Tenant settings"
4. Find "Developer settings" section
5. Enable these settings:
   - **"Service principals can use Power BI APIs"**
   - **"Service principals can access read-only Power BI admin APIs"**
   - **"Allow service principals to use Power BI APIs"**
6. Apply to:
   - Entire organization, OR
   - Specific security groups (add your service principal to the group)

### Step 4: Add Service Principal to Workspaces

For EACH workspace you want to access:
1. Go to the workspace in Power BI
2. Click "Manage access" 
3. Add the service principal (search by app name or ID)
4. Grant **Member** role (not Viewer)

### Step 5: Verify Permissions

Check your app registration shows:
```
Power BI Service
- Tenant.Read.All    ✓ Granted for [Organization]
- Dataset.Read.All   ✓ Granted for [Organization]
- Workspace.Read.All ✓ Granted for [Organization]
```

### Step 6: Test Again

After completing all steps:
1. Wait 5-10 minutes for permissions to propagate
2. Try the API calls again
3. The 403 error should be resolved

## Common Mistakes

1. **Using Delegated permissions instead of Application permissions**
   - Service principals need Application permissions
   
2. **Forgetting to grant admin consent**
   - Permissions won't work without admin consent
   
3. **Not enabling in Power BI Admin Portal**
   - Even with Azure AD permissions, Power BI blocks service principals by default
   
4. **Only adding to workspace as Viewer**
   - Service principals need Member role for API access

## Verification Script

Run this to check if permissions are working:
```bash
python test_powerbi_auth.py
```

Expected output should show:
- ✓ Token acquired
- ✓ Workspaces listed
- ✓ Datasets listed
- ✓ Query executed