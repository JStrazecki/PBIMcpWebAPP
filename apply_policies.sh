#!/bin/bash
# Apply security policies to MCP API

# Configuration
RESOURCE_GROUP="rg-pbi-mcp-enterprise"
APIM_NAME="your-apim-name"
API_ID="powerbi-mcp-api"

echo "🔐 Applying security policies to MCP API..."

# Apply API-level policy
echo "📋 Applying API-level security policy..."

az apim api policy create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id $API_ID \
  --policy-content "$(cat mcp_api_policies.xml)"

if [ $? -ne 0 ]; then
    echo "❌ Failed to apply API policy"
    exit 1
fi

echo "✅ API-level policy applied successfully!"

# Apply operation-specific policies for OAuth endpoints
echo "🔧 Applying OAuth-specific policies..."

# OAuth authorize endpoint policy (no JWT validation needed)
cat > oauth_authorize_policy.xml << 'EOF'
<policies>
    <inbound>
        <base />
        <!-- Allow OAuth authorization without JWT -->
        <set-header name="Authorization" exists-action="delete" />
        <rate-limit calls="50" renewal-period="60" />
    </inbound>
    <backend>
        <base />
    </backend>
    <outbound>
        <base />
    </outbound>
    <on-error>
        <base />
    </on-error>
</policies>
EOF

az apim api operation policy create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id $API_ID \
  --operation-id "authorize" \
  --policy-content "$(cat oauth_authorize_policy.xml)"

# OAuth callback endpoint policy  
cat > oauth_callback_policy.xml << 'EOF'
<policies>
    <inbound>
        <base />
        <!-- Allow OAuth callback without JWT -->
        <set-header name="Authorization" exists-action="delete" />
        <rate-limit calls="50" renewal-period="60" />
    </inbound>
    <backend>
        <base />
    </backend>
    <outbound>
        <base />
    </outbound>
    <on-error>
        <base />
    </on-error>
</policies>
EOF

az apim api operation policy create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id $API_ID \
  --operation-id "oauth-callback" \
  --policy-content "$(cat oauth_callback_policy.xml)"

echo "✅ OAuth policies applied successfully!"

# Clean up temporary files
rm -f oauth_authorize_policy.xml oauth_callback_policy.xml

# Get gateway URL for testing
GATEWAY_URL=$(az apim show \
  --resource-group $RESOURCE_GROUP \
  --name $APIM_NAME \
  --query "gatewayUrl" \
  --output tsv)

echo ""
echo "🎉 Security Policies Applied Successfully!"
echo ""
echo "📡 API Endpoints:"
echo "  Health:     $GATEWAY_URL/powerbi-mcp/health"
echo "  Status:     $GATEWAY_URL/powerbi-mcp/mcp/status"
echo "  Workspaces: $GATEWAY_URL/powerbi-mcp/mcp/workspaces"
echo "  Datasets:   $GATEWAY_URL/powerbi-mcp/mcp/datasets"
echo "  Query:      $GATEWAY_URL/powerbi-mcp/mcp/query"
echo "  Authorize:  $GATEWAY_URL/powerbi-mcp/authorize"
echo "  Callback:   $GATEWAY_URL/powerbi-mcp/auth/callback"
echo ""
echo "🔐 Security Features Applied:"
echo "  ✅ JWT token validation"
echo "  ✅ Rate limiting (100 calls/min)"
echo "  ✅ CORS for Claude.ai"
echo "  ✅ Security headers"
echo "  ✅ Request/response logging"
echo "  ✅ Error handling"
echo ""
echo "🔄 Next: Configure Claude.ai Enterprise integration"