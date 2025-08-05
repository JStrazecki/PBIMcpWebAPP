# Connecting Power BI MCP Server to Claude.ai

This guide will walk you through connecting your deployed Power BI MCP Server to Claude.ai.

## Prerequisites

- ✅ Power BI MCP Server deployed and running on Azure
- ✅ Azure App Service URL (e.g., `https://your-app-name.azurewebsites.net`)
- ✅ Claude.ai account with MCP feature access

## Step 1: Verify Your MCP Server is Running

Before connecting to Claude.ai, ensure your server is working:

```bash
# Test the health endpoint
curl https://your-app-name.azurewebsites.net/health

# Expected response:
# {"status": "ok", "server": "Power BI MCP Server", "transport": "http"}
```

## Step 2: Add MCP Server in Claude.ai

1. **Open Claude.ai** in your web browser
2. **Click on your profile** icon in the bottom left corner
3. **Select "Settings"** from the menu
4. **Navigate to "Developer"** section
5. **Click on "Model Context Protocol (MCP)"**

## Step 3: Configure the MCP Connection

1. **Click "Add MCP Server"** button
2. **Fill in the connection details:**
   - **Name**: `Power BI MCP Server` (or any name you prefer)
   - **URL**: `https://your-app-name.azurewebsites.net/mcp`
   - **Authentication**: Leave empty (no authentication required)

3. **Click "Connect"** to establish the connection

## Step 4: Verify the Connection

Once connected, you should see:
- ✅ Green status indicator showing "Connected"
- ✅ List of available tools:
  - `powerbi_health` - Check server health
  - `powerbi_workspaces` - List workspaces
  - `powerbi_datasets` - List datasets
  - `powerbi_query` - Execute DAX queries

## Step 5: Test the Integration

In a new Claude.ai conversation, try these commands:

### Test 1: Check Server Health
```
Can you check the Power BI server health?
```
Claude should use the `powerbi_health` tool and show the server status.

### Test 2: List Workspaces
```
Show me the available Power BI workspaces
```
Claude should use the `powerbi_workspaces` tool and display workspaces (or demo data).

### Test 3: List Datasets
```
What datasets are available in Power BI?
```
Claude should use the `powerbi_datasets` tool to show available datasets.

### Test 4: Run a Query (Demo Mode)
```
Can you run a simple DAX query to get sales data?
```
Claude should use the `powerbi_query` tool with a sample query.

## Troubleshooting

### Connection Failed

If Claude.ai can't connect to your MCP server:

1. **Check the URL**:
   - Ensure you're using `/mcp` at the end
   - Verify HTTPS (not HTTP)
   - No trailing slash

2. **Verify Server is Running**:
   ```bash
   curl -X POST https://your-app-name.azurewebsites.net/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}'
   ```
   Should return a JSON response with server info.

3. **Check Azure Logs**:
   - Go to Azure Portal > Your App Service > Log stream
   - Look for incoming requests from Claude.ai

### Tools Not Appearing

If connected but tools aren't showing:

1. **Refresh the connection**:
   - Disconnect and reconnect the MCP server
   - Refresh the Claude.ai page

2. **Check tool registration**:
   - Tools should be automatically discovered
   - No manual registration needed

### Authentication Errors

This implementation has no authentication requirements. If you see auth errors:

1. **Ensure you left authentication fields empty** in Claude.ai
2. **Check you're using the FastMCP implementation** (not the Flask version)

## Demo Mode vs Production Mode

### Demo Mode (Default)
When Power BI credentials are not configured:
- All tools return sample/demo data
- No actual Power BI connection
- Perfect for testing the integration

### Production Mode
To connect to real Power BI data:

1. **Set environment variables** in Azure App Service:
   - `AZURE_CLIENT_ID` - Your Power BI app registration
   - `AZURE_CLIENT_SECRET` - Your app secret
   - `AZURE_TENANT_ID` - Your Azure tenant ID

2. **Restart the App Service** to apply changes

3. **Grant permissions** to your app registration:
   - Power BI Service permissions
   - Workspace access for the service principal

## Security Considerations

1. **HTTPS Only**: Always use HTTPS URLs
2. **No Authentication**: This implementation has no auth layer
3. **Public Access**: Anyone with the URL can access the MCP server
4. **Demo Data**: Safe to use for testing without exposing real data

## Advanced Configuration

### Custom Port or Path

If you need to change the default configuration:

1. **Port**: Set via `PORT` environment variable in Azure
2. **Path**: Currently hardcoded to `/mcp` in `run_fastmcp.py`

### Logging and Monitoring

View server logs in Azure:
1. Azure Portal > App Service > Log stream
2. Or use Azure CLI: `az webapp log tail --name your-app-name --resource-group your-rg`

## Common Use Cases

### 1. Query Sales Data
```
"Show me total sales by region using DAX"
```

### 2. List All Reports
```
"What Power BI reports are available in my workspaces?"
```

### 3. Dataset Information
```
"Tell me about the datasets in workspace XYZ"
```

### 4. Health Monitoring
```
"Is the Power BI server healthy and what's its configuration?"
```

## Need Help?

- **Server Issues**: Check `FASTMCP_DEPLOYMENT_LOG.md` for deployment troubleshooting
- **Connection Issues**: Verify URL format and server availability
- **Tool Issues**: Ensure FastMCP server is running latest version

---

Last Updated: 2025-08-05