#!/bin/bash
# Create MCP Proxy API for Power BI integration

# Configuration (update these with your values)
RESOURCE_GROUP="rg-pbi-mcp-enterprise"
APIM_NAME="your-apim-name"  # From step 1
BACKEND_URL="https://pbimcp.azurewebsites.net"  # Your existing Azure Web App
TENANT_ID="your-tenant-id"

echo "🔧 Creating MCP Proxy API..."
echo "📋 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  APIM Name: $APIM_NAME"
echo "  Backend URL: $BACKEND_URL"
echo ""

# Create the API
echo "📡 Creating Power BI MCP API..."

az apim api create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id "powerbi-mcp-api" \
  --display-name "Power BI MCP API" \
  --description "Secure gateway for Power BI MCP Server" \
  --path "powerbi-mcp" \
  --protocols "https" \
  --service-url $BACKEND_URL

if [ $? -ne 0 ]; then
    echo "❌ Failed to create API"
    exit 1
fi

echo "✅ API created successfully!"

# Create operations for MCP endpoints
echo "🔧 Creating API operations..."

# Health endpoint
az apim api operation create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id "powerbi-mcp-api" \
  --operation-id "health" \
  --display-name "Health Check" \
  --method "GET" \
  --url-template "/health"

# MCP Status endpoint
az apim api operation create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id "powerbi-mcp-api" \
  --operation-id "mcp-status" \
  --display-name "MCP Status" \
  --method "GET" \
  --url-template "/mcp/status"

# Workspaces endpoint
az apim api operation create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id "powerbi-mcp-api" \
  --operation-id "workspaces" \
  --display-name "List Workspaces" \
  --method "GET" \
  --url-template "/mcp/workspaces"

# Datasets endpoint
az apim api operation create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id "powerbi-mcp-api" \
  --operation-id "datasets" \
  --display-name "List Datasets" \
  --method "GET" \
  --url-template "/mcp/datasets"

# Query endpoint
az apim api operation create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id "powerbi-mcp-api" \
  --operation-id "query" \
  --display-name "Execute Query" \
  --method "POST" \
  --url-template "/mcp/query"

# OAuth authorize endpoint
az apim api operation create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id "powerbi-mcp-api" \
  --operation-id "authorize" \
  --display-name "OAuth Authorize" \
  --method "GET" \
  --url-template "/authorize"

# OAuth callback endpoint
az apim api operation create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id "powerbi-mcp-api" \
  --operation-id "oauth-callback" \
  --display-name "OAuth Callback" \
  --method "GET" \
  --url-template "/auth/callback"

echo "✅ API operations created successfully!"

echo ""
echo "🎉 MCP Proxy API Creation Complete!"
echo "📡 API Base URL: \$(GATEWAY_URL)/powerbi-mcp"
echo ""
echo "🔄 Next: Apply security policies"