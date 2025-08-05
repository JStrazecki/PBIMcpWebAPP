# Claude.ai Power BI MCP Server Setup Guide

## Quick Start

Your Power BI MCP Server is deployed and ready at: **https://pbimcp.azurewebsites.net**

### 1. Connect to Claude.ai

1. Open [Claude.ai](https://claude.ai) in your browser
2. Click your profile icon (bottom left) → Settings → Developer → Model Context Protocol (MCP)
3. Click "Add MCP Server"
4. Enter:
   - **Name**: Power BI MCP Server
   - **URL**: `https://pbimcp.azurewebsites.net/mcp`
   - **Authentication**: Leave empty
5. Click "Connect"

### 2. Verify Connection

You should see:
- ✅ Green "Connected" status
- ✅ 4 available tools listed

### 3. Test the Tools

Try these commands in Claude:

```
"Check the Power BI server health"
"Show me available Power BI workspaces"
"List all Power BI datasets"
"Run a DAX query to get sales data"
```

## Available Tools

| Tool | Description | Demo Mode |
|------|-------------|-----------|
| `powerbi_health` | Check server status | Returns config info |
| `powerbi_workspaces` | List workspaces | Returns 3 demo workspaces |
| `powerbi_datasets` | Get datasets | Returns sample datasets |
| `powerbi_query` | Execute DAX queries | Returns mock results |

## Server Status

- **URL**: https://pbimcp.azurewebsites.net
- **Status**: ✅ Operational
- **Mode**: Demo (no Power BI credentials configured)
- **FastMCP Version**: 2.11.1
- **MCP Protocol**: 1.12.3

## Troubleshooting

### Connection Failed
- Ensure URL ends with `/mcp` (no trailing slash)
- Verify: `https://pbimcp.azurewebsites.net/health` returns 200 OK
- Leave authentication fields empty

### Tools Not Showing
- Disconnect and reconnect the server
- Refresh your Claude.ai page
- Check server logs in Azure Portal

### Getting Real Power BI Data

To connect to actual Power BI data instead of demo mode:

1. Create Azure App Registration with Power BI permissions
2. Set these environment variables in Azure App Service:
   - `AZURE_CLIENT_ID`
   - `AZURE_CLIENT_SECRET`
   - `AZURE_TENANT_ID`
3. Grant app access to Power BI workspaces
4. Restart the App Service

## Technical Details

- **Transport**: Server-Sent Events (SSE)
- **Authentication**: None (public access)
- **Session Management**: Automatic via MCP protocol
- **Endpoints**:
  - `/` - Server info
  - `/health` - Health check
  - `/mcp/` - MCP protocol endpoint

## Support

- **Logs**: Azure Portal → App Service → Log stream
- **Test endpoint**: `curl https://pbimcp.azurewebsites.net/health`
- **Deployment details**: See `FASTMCP_DEPLOYMENT_LOG.md`

---
Last Updated: 2025-08-05