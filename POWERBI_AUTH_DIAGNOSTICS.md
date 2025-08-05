# Power BI Authentication Diagnostics

## Current Situation

From the conversation logs:
1. ✅ Token acquisition works (can authenticate)
2. ✅ List workspaces works 
3. ✅ List datasets works
4. ❌ Query dataset fails with different errors:
   - Dataset 1: 400 - "Failed to open the MSOLAP connection"
   - Dataset 2: 404 - "Dataset not found"

## Possible Root Causes

### 1. Dataset-Specific Permissions
Even if you have workspace access, datasets can have additional security:
- Row-Level Security (RLS) might be blocking the service principal
- Dataset-specific permissions might be missing
- The dataset might require specific roles

### 2. API Differences
The error "Failed to open the MSOLAP connection" suggests the dataset might be:
- In DirectQuery mode (not Import mode)
- Using a live connection to Analysis Services
- Requiring specific connection settings

### 3. Service Principal Configuration
The service principal might need:
- To be explicitly added to each dataset's security settings
- Build permissions on the dataset (not just Read)
- To be part of a security group with proper permissions

### 4. Azure-Specific Issues
When running on Azure App Service:
- Network restrictions might block connections to data sources
- Managed Identity might interfere with service principal auth
- Regional restrictions might apply

## Diagnostic Steps

### Step 1: Run the Test Script
```bash
python test_powerbi_auth.py
```

This will show:
- If token acquisition works
- What permissions the token has
- Which API calls succeed/fail
- Detailed error messages

### Step 2: Check Dataset Configuration
In Power BI Service:
1. Go to dataset settings
2. Check "Data source credentials"
3. Check "Security" → "Row-level security"
4. Check "Settings" → "Query caching"

### Step 3: Test with Power BI REST API Explorer
1. Go to https://docs.microsoft.com/en-us/rest/api/power-bi/
2. Use "Try It" feature
3. Test the same query with your credentials
4. Compare results

### Step 4: Check Service Principal Permissions
```powershell
# In Azure Portal or PowerShell
# Check App Registration API permissions
# Should have:
# - Power BI Service → Dataset.Read.All (Application)
# - Power BI Service → Workspace.Read.All (Application)
```

### Step 5: Test Direct Dataset Access
Try accessing the dataset without workspace context:
```python
# Use dataset ID directly without workspace
url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/executeQueries"
```

## Key Differences from Local

When it "worked locally", it might have been:
1. Using a user token instead of service principal
2. Running with different permissions
3. Accessing different datasets
4. Using a different authentication flow

## Solution Paths

### Option 1: Dataset Security Settings
1. In Power BI Service, go to dataset settings
2. Add service principal to dataset security
3. Grant "Build" permission

### Option 2: Use Admin APIs
If you have admin access:
```python
# Use admin API endpoint
url = f"https://api.powerbi.com/v1.0/myorg/admin/datasets/{dataset_id}/executeQueries"
```

### Option 3: Alternative Authentication
1. Use delegated permissions (user context)
2. Use Power BI Embedded token
3. Use managed identity

## Next Steps

1. Run `test_powerbi_auth.py` and share results
2. Check exact dataset configuration in Power BI
3. Verify service principal has "Build" permission on datasets
4. Try query on a simple test dataset first