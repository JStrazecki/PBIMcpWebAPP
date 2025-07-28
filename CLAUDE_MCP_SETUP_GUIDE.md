# 🔗 Connect Your Power BI MCP Server to Claude.ai

## Step-by-Step Setup Guide

### 1. Access Claude.ai MCP Settings
1. Go to **Claude.ai** in your browser
2. Click your **profile/settings** icon
3. Navigate to **"Model Context Protocol (MCP)"** or **"Integrations"**
4. Click **"Add Custom Connector"** or **"+ Add MCP Server"**

### 2. Configure Your MCP Connection

Fill in these **exact values**:

#### **Server Name:**
```
Power BI Finance Server
```

#### **Remote MCP Server URL:**
```
https://pbimcp.azurewebsites.net
```

#### **OAuth Client ID:** (Leave Empty)
```
(Leave blank - not required)
```

#### **OAuth Client Secret:** (Leave Empty) 
```
(Leave blank - not required)
```

#### **Description:** (Optional)
```
Power BI MCP server for financial data analysis and reporting
```

### 3. Connection Settings

- **Authentication Type:** None/Public (your server doesn't require OAuth)
- **Protocol:** HTTP/HTTPS
- **Port:** Default (443 for HTTPS)

### 4. Test the Connection

After adding the connector:

1. **Save** the configuration
2. **Test Connection** - should show ✅ Connected
3. You should see these available tools:
   - `get_powerbi_status` - Check Power BI authentication status
   - `health_check` - System health verification
   - `list_powerbi_workspaces` - List available workspaces
   - `get_powerbi_datasets` - Get datasets from workspaces  
   - `execute_powerbi_query` - Execute DAX/M queries

### 5. Using Your MCP Server in Claude

Once connected, you can ask Claude:

```
"Check my Power BI server status"
"List my Power BI workspaces"
"Show me the available datasets"
"Run a health check on my Power BI connection"
```

Claude will automatically use your MCP server tools to respond.

### 6. Power BI Authentication Setup (Optional)

To enable full Power BI functionality, configure these environment variables in Azure Portal → Configuration → Application Settings:

```
POWERBI_CLIENT_ID=your-power-bi-app-client-id
POWERBI_CLIENT_SECRET=your-power-bi-app-secret
POWERBI_TENANT_ID=your-azure-tenant-id
```

Or use a manual token:
```
POWERBI_TOKEN=your-power-bi-bearer-token
```

### 7. Troubleshooting

**If connection fails:**

1. **Verify URL:** Ensure `https://pbimcp.azurewebsites.net` is accessible
2. **Check Server Status:** Visit the URL directly - should show JSON response
3. **Azure Status:** Verify your Azure Web App is running
4. **Retry:** Sometimes Claude.ai needs a moment - try reconnecting

**Test your server directly:**
- Visit: https://pbimcp.azurewebsites.net/health
- Should return: `{"status": "healthy", ...}`

## Expected Result

✅ **Successful Connection:**
- Claude.ai shows "Connected" status
- MCP tools appear in Claude's available functions
- You can ask Claude to use Power BI data via your MCP server

Your Power BI MCP server is now integrated with Claude.ai! 🎉