#!/bin/bash
# Configure OAuth 2.0 for API Management with Entra ID

# Configuration (update these with your values)
RESOURCE_GROUP="rg-pbi-mcp-enterprise"
APIM_NAME="your-apim-name"  # From previous step
TENANT_ID="your-tenant-id"
CLIENT_ID="5bdb10bc-bb29-4af9-8cb5-062690e6be15"  # Your existing app registration
CLIENT_SECRET="your-client-secret"

echo "🔐 Configuring OAuth 2.0 for API Management..."
echo "📋 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  APIM Name: $APIM_NAME" 
echo "  Tenant ID: $TENANT_ID"
echo "  Client ID: $CLIENT_ID"
echo ""

# Create OAuth 2.0 authorization server
echo "🔧 Creating OAuth 2.0 authorization server..."

az apim oauth2-server create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --server-id "powerbi-oauth-server" \
  --display-name "Power BI OAuth Server" \
  --description "OAuth 2.0 server for Power BI MCP access" \
  --client-registration-endpoint "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/authorize" \
  --authorization-endpoint "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/authorize" \
  --token-endpoint "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token" \
  --client-id $CLIENT_ID \
  --client-secret $CLIENT_SECRET \
  --authorization-methods "GET,POST" \
  --grant-types "authorizationCode,clientCredentials" \
  --scopes "https://analysis.windows.net/powerbi/api/.default" \
  --default-scope "https://analysis.windows.net/powerbi/api/.default"

if [ $? -ne 0 ]; then
    echo "❌ Failed to create OAuth server"
    exit 1
fi

echo "✅ OAuth 2.0 server created successfully!"

# Create Named Values for secure configuration
echo "🔧 Creating named values for secure configuration..."

az apim nv create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --named-value-id "powerbi-tenant-id" \
  --display-name "PowerBI-Tenant-ID" \
  --value $TENANT_ID

az apim nv create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --named-value-id "powerbi-client-id" \
  --display-name "PowerBI-Client-ID" \
  --value $CLIENT_ID

az apim nv create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --named-value-id "powerbi-client-secret" \
  --display-name "PowerBI-Client-Secret" \
  --value $CLIENT_SECRET \
  --secret true

echo "✅ Named values created successfully!"

# Get APIM gateway URL for next steps
GATEWAY_URL=$(az apim show \
  --resource-group $RESOURCE_GROUP \
  --name $APIM_NAME \
  --query "gatewayUrl" \
  --output tsv)

echo ""
echo "🎉 OAuth 2.0 Configuration Complete!"
echo "📍 Gateway URL: $GATEWAY_URL"
echo "🔐 OAuth Server ID: powerbi-oauth-server"
echo ""
echo "📝 Important URLs to configure in your app registration:"
echo "  Redirect URI: $GATEWAY_URL/powerbi-mcp/oauth/callback"
echo "  Web API: $GATEWAY_URL/powerbi-mcp/*"
echo ""
echo "🔄 Next: Create MCP Proxy API and policies"