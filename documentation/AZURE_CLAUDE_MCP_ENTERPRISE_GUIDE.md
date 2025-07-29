# Claude.ai Enterprise MCP Server Configuration Guide for Azure

## Problem Analysis

Your Azure MCP server is **working perfectly** - all endpoints return correct data and Power BI authentication is successful. However, Claude.ai Enterprise cannot connect because of a **protocol mismatch**.

**Current Setup:** HTTP-to-MCP Bridge on Azure Web Apps  
**Claude.ai Expects:** Native MCP Server with stdio transport

## Root Cause

Claude.ai Enterprise MCP integration requires:
1. **Native MCP Protocol** (not HTTP endpoints)
2. **STDIO transport** (standard input/output) 
3. **Direct process communication** (not web requests)

Azure Web Apps only support HTTP protocols, not direct stdio communication that Claude.ai expects.

## Solution Options

### Option 1: Azure Container Apps with MCP Server (Recommended)

Azure Container Apps can run native MCP servers with stdio transport:

#### Step 1: Create Dockerfile for MCP Server
```dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy MCP server code
COPY mcp_server.py .
COPY pbi_mcp_finance/ ./pbi_mcp_finance/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run MCP server with stdio transport
CMD ["python", "mcp_server.py"]
```

#### Step 2: Deploy to Azure Container Apps
```bash
# Create resource group
az group create --name rg-pbi-mcp --location eastus

# Create container app environment
az containerapp env create \
  --name pbi-mcp-env \
  --resource-group rg-pbi-mcp \
  --location eastus

# Deploy container app
az containerapp create \
  --name pbi-mcp-server \
  --resource-group rg-pbi-mcp \
  --environment pbi-mcp-env \
  --image your-registry/pbi-mcp-server:latest \
  --env-vars AZURE_CLIENT_ID=secretref:azure-client-id \
             AZURE_CLIENT_SECRET=secretref:azure-client-secret \
             AZURE_TENANT_ID=secretref:azure-tenant-id \
  --secrets azure-client-id=your-client-id \
             azure-client-secret=your-client-secret \
             azure-tenant-id=your-tenant-id
```

#### Step 3: Configure Claude.ai
```json
{
  "mcpServers": {
    "powerbi-server": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "your-registry/pbi-mcp-server:latest"],
      "env": {
        "AZURE_CLIENT_ID": "your-client-id",
        "AZURE_CLIENT_SECRET": "your-client-secret", 
        "AZURE_TENANT_ID": "your-tenant-id"
      }
    }
  }
}
```

### Option 2: Azure API Management as OAuth Gateway (Enterprise)

For enterprise-grade security, use Azure API Management:

#### Step 1: Create API Management Instance
```bash
az apim create \
  --resource-group rg-pbi-mcp \
  --name pbi-mcp-apim \
  --publisher-email admin@company.com \
  --publisher-name "Company Name" \
  --sku-name Developer
```

#### Step 2: Configure OAuth 2.0 with Entra ID
1. Go to Azure Portal → API Management → APIs → OAuth 2.0
2. Add OAuth 2.0 server:
   - **Authorization endpoint:** `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/authorize`
   - **Token endpoint:** `https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token`
   - **Scopes:** `https://analysis.windows.net/powerbi/api/.default`

#### Step 3: Create MCP Proxy API
```xml
<policies>
    <inbound>
        <validate-jwt>
            <openid-config url="https://login.microsoftonline.com/{tenant-id}/v2.0/.well-known/openid-configuration" />
        </validate-jwt>
        <set-backend-service base-url="https://your-mcp-server.azurecontainerapps.io" />
    </inbound>
</policies>
```

### Option 3: Local MCP Server (Development)

For development/testing, run MCP server locally:

#### Step 1: Run Local MCP Server
```bash
cd C:\Users\Dom\Documents\GitHub\PBIMcpWebAPP
python mcp_server.py
```

#### Step 2: Configure Claude Desktop
Create/update `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "powerbi-server": {
      "command": "python",
      "args": ["C:\\Users\\Dom\\Documents\\GitHub\\PBIMcpWebAPP\\mcp_server.py"],
      "env": {
        "AZURE_CLIENT_ID": "your-client-id",
        "AZURE_CLIENT_SECRET": "your-client-secret",
        "AZURE_TENANT_ID": "your-tenant-id"
      }
    }
  }
}
```

## Current Server Status

Your Azure HTTP server is working correctly:
- ✅ Authentication: Configured and working
- ✅ Power BI Access: Granted  
- ✅ Workspaces: 2 workspaces accessible
- ✅ All endpoints functional

The issue is **not with your server** - it's with the transport protocol mismatch.

## Recommended Approach

1. **Short-term:** Use Option 3 (Local MCP Server) for immediate testing
2. **Long-term:** Implement Option 1 (Azure Container Apps) for production deployment
3. **Enterprise:** Consider Option 2 (API Management) for advanced security requirements

## Configuration Files to Update

### For Azure Container Apps:
- Update `mcp_server.py` to ensure proper stdio handling
- Create `Dockerfile` for containerization
- Set up Azure Container Registry

### For Local Development:
- Use existing `mcp_server.py` 
- Configure Claude Desktop with correct paths
- Set environment variables locally

## Technical Notes

- **Transport Protocol:** Claude.ai requires stdio, not HTTP
- **Authentication:** Your OAuth setup is correct and working
- **Power BI Integration:** All API calls are successful
- **Azure Limitation:** Web Apps don't support stdio transport

Your current setup demonstrates that all the authentication and Power BI integration logic is working perfectly. The only change needed is the transport layer to make it compatible with Claude.ai's MCP expectations.