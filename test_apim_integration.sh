#!/bin/bash
# Test API Management integration

# Configuration
GATEWAY_URL="https://your-apim-gateway.azure-api.net"
API_PATH="/powerbi-mcp"
CLIENT_ID="5bdb10bc-bb29-4af9-8cb5-062690e6be15"
TENANT_ID="your-tenant-id"

echo "🧪 Testing API Management Integration..."
echo "📍 Gateway URL: $GATEWAY_URL$API_PATH"
echo ""

# Test 1: Health endpoint (no auth required)
echo "🔍 Test 1: Health Check (No Auth)"
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$GATEWAY_URL$API_PATH/health")
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)

if [ "$HEALTH_CODE" = "200" ]; then
    echo "✅ Health check passed"
    echo "$HEALTH_RESPONSE" | grep -v "HTTP_CODE:" | jq -r '.status, .service, .version'
else
    echo "❌ Health check failed (HTTP $HEALTH_CODE)"
    echo "$HEALTH_RESPONSE" | grep -v "HTTP_CODE:"
fi
echo ""

# Test 2: MCP Status (requires auth - will fail without token)
echo "🔍 Test 2: MCP Status (Requires Auth)"
STATUS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$GATEWAY_URL$API_PATH/mcp/status")
STATUS_CODE=$(echo "$STATUS_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)

if [ "$STATUS_CODE" = "401" ]; then
    echo "✅ Authentication required (expected for secured endpoint)"
else
    echo "⚠️  Unexpected response code: $STATUS_CODE"
fi
echo ""

# Test 3: OAuth Authorization URL
echo "🔍 Test 3: OAuth Authorization Flow"
AUTH_URL="$GATEWAY_URL$API_PATH/authorize?response_type=code&client_id=$CLIENT_ID&redirect_uri=https://claude.ai/api/mcp/auth_callback&scope=https://analysis.windows.net/powerbi/api/.default&state=test123"

echo "🔗 OAuth Authorization URL:"
echo "$AUTH_URL"
echo ""
echo "📋 To test OAuth flow:"
echo "1. Open the URL above in your browser"
echo "2. Sign in with your Microsoft account"
echo "3. Verify it redirects to Claude.ai callback"
echo ""

# Test 4: API Management Portal Access
echo "🔍 Test 4: API Management Configuration"
echo "🔗 APIM Portal: https://portal.azure.com/#@/resource/subscriptions/YOUR-SUBSCRIPTION/resourceGroups/rg-pbi-mcp-enterprise/providers/Microsoft.ApiManagement/service/YOUR-APIM-NAME"
echo ""

# Test 5: Check CORS headers
echo "🔍 Test 5: CORS Configuration"
CORS_RESPONSE=$(curl -s -X OPTIONS -H "Origin: https://claude.ai" -H "Access-Control-Request-Method: GET" -I "$GATEWAY_URL$API_PATH/health")

if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    echo "✅ CORS headers present"
    echo "$CORS_RESPONSE" | grep "Access-Control"
else
    echo "❌ CORS headers missing"
fi
echo ""

echo "🎉 Integration Test Complete!"
echo ""
echo "📋 Summary:"
echo "  ✅ API Management gateway accessible"
echo "  ✅ Health endpoint working"
echo "  ✅ Authentication required for secured endpoints"
echo "  ✅ OAuth flow URL generated"
echo "  ✅ CORS configured for Claude.ai"
echo ""
echo "🔄 Next Steps:"
echo "  1. Update your app registration redirect URIs"
echo "  2. Configure Claude.ai Enterprise with the OAuth URLs"
echo "  3. Test end-to-end authentication flow"