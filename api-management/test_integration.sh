#!/bin/bash
# Test API Management Integration - NO MANUAL CONFIGURATION
# Automatically discovers configuration from previous scripts

set -e

# Try to auto-discover configuration
WEBAPP_NAME="pbimcp"
RESOURCE_GROUP_NAME="rg-pbi-mcp-enterprise"

# Colors for output  
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_step() { echo -e "${YELLOW}📋 $1${NC}"; }

echo -e "${GREEN}🧪 API Management Integration Testing (Fully Automated)${NC}"
echo -e "${GREEN}====================================================${NC}"

# Step 1: Auto-discover API Management instance
print_step "Step 1: Auto-discovering Configuration"

APIM_NAME=$(az apim list --resource-group "$RESOURCE_GROUP_NAME" --query "[0].name" -o tsv 2>/dev/null)
if [ -z "$APIM_NAME" ]; then
    print_error "No API Management instance found in resource group '$RESOURCE_GROUP_NAME'"
    print_info "Available API Management instances:"
    az apim list --query "[].{Name:name, ResourceGroup:resourceGroup}" -o table
    exit 1
fi

print_status "Auto-detected API Management: $APIM_NAME"

# Get gateway URL and API details
GATEWAY_URL=$(az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query "gatewayUrl" -o tsv)
API_PATH="powerbi-mcp"
BASE_URL="$GATEWAY_URL/$API_PATH"

print_status "Configuration discovered:"
print_info "Gateway URL: $GATEWAY_URL"
print_info "API Base URL: $BASE_URL"

# Step 2: Get OAuth configuration from Web App
print_step "Step 2: Retrieving OAuth Configuration from Web App"

WEBAPP_RG=$(az webapp list --query "[?name=='$WEBAPP_NAME'].resourceGroup" -o tsv | head -1)
if [ -z "$WEBAPP_RG" ]; then
    print_warning "Web App '$WEBAPP_NAME' not found - OAuth tests will be skipped"
    OAUTH_AVAILABLE=false
else
    TENANT_ID=$(az webapp config appsettings list --name "$WEBAPP_NAME" --resource-group "$WEBAPP_RG" --query "[?name=='AZURE_TENANT_ID'].value" -o tsv)
    CLIENT_ID=$(az webapp config appsettings list --name "$WEBAPP_NAME" --resource-group "$WEBAPP_RG" --query "[?name=='AZURE_CLIENT_ID'].value" -o tsv)
    
    if [ -n "$TENANT_ID" ] && [ -n "$CLIENT_ID" ]; then
        print_status "OAuth configuration retrieved from Web App"
        print_info "Tenant ID: ${TENANT_ID:0:8}..."
        print_info "Client ID: ${CLIENT_ID:0:8}..."
        OAUTH_AVAILABLE=true
    else
        print_warning "OAuth configuration incomplete in Web App - OAuth tests will be limited"
        OAUTH_AVAILABLE=false
    fi
fi

# Step 3: Run comprehensive tests
print_step "Step 3: Running Integration Tests"

# Test 1: Health Check
print_info "Test 1: Health Check Endpoint"
if curl -s --max-time 10 "$BASE_URL/health" > /dev/null 2>&1; then
    print_status "✅ Health endpoint accessible"
    
    HEALTH_RESPONSE=$(curl -s --max-time 10 "$BASE_URL/health")
    if echo "$HEALTH_RESPONSE" | grep -q "healthy\\|status\\|service"; then
        print_status "✅ Health endpoint returns valid response"
    else
        print_warning "Health endpoint responds but content may be unexpected"
    fi
else
    print_error "❌ Health endpoint not accessible"
fi

# Test 2: Root endpoint  
print_info "Test 2: Root Endpoint"
if curl -s --max-time 10 "$BASE_URL/" > /dev/null 2>&1; then
    print_status "✅ Root endpoint accessible"
else
    print_warning "Root endpoint not accessible (may be expected)"
fi

# Test 3: Protected endpoint authentication
print_info "Test 3: Protected Endpoint Authentication"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$BASE_URL/mcp/status")
if [ "$HTTP_STATUS" = "401" ]; then
    print_status "✅ Protected endpoint correctly requires authentication (401)"
elif [ "$HTTP_STATUS" = "200" ]; then
    print_warning "⚠️  Protected endpoint accessible without authentication (potential security issue)"
else
    print_info "ℹ️  Protected endpoint returned status: $HTTP_STATUS"
fi

# Test 4: CORS Configuration
print_info "Test 4: CORS Configuration for Claude.ai"
CORS_RESPONSE=$(curl -s -H "Origin: https://claude.ai" -H "Access-Control-Request-Method: GET" -X OPTIONS "$BASE_URL/health" -D - 2>/dev/null || true)
if echo "$CORS_RESPONSE" | grep -iq "access-control-allow-origin"; then
    print_status "✅ CORS headers present for Claude.ai"
else
    print_warning "⚠️  CORS headers not detected (may affect Claude.ai integration)"
fi

# Test 5: OAuth Authorization (if configuration available)
if [ "$OAUTH_AVAILABLE" = true ]; then
    print_info "Test 5: OAuth Authorization Endpoint"
    AUTH_URL="$BASE_URL/authorize?response_type=code&client_id=$CLIENT_ID&redirect_uri=https://claude.ai/api/mcp/auth_callback&scope=https://analysis.windows.net/powerbi/api/.default"
    
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$AUTH_URL")
    if [ "$HTTP_STATUS" = "302" ] || [ "$HTTP_STATUS" = "301" ]; then
        print_status "✅ OAuth authorization endpoint redirects correctly ($HTTP_STATUS)"
    else
        print_warning "⚠️  OAuth authorization returned status: $HTTP_STATUS (expected 302)"
    fi
else
    print_info "Test 5: OAuth Authorization - Skipped (configuration not available)"
fi

# Test 6: API Management Developer Portal
print_info "Test 6: Developer Portal"
if [[ "$GATEWAY_URL" =~ https://([^.]+)\.azure-api\.net ]]; then
    APIM_INSTANCE="${BASH_REMATCH[1]}"
    DEVELOPER_PORTAL="https://$APIM_INSTANCE.developer.azure-api.net"
    
    if curl -s --max-time 10 "$DEVELOPER_PORTAL" > /dev/null 2>&1; then
        print_status "✅ Developer portal accessible: $DEVELOPER_PORTAL"
    else
        print_info "ℹ️  Developer portal: $DEVELOPER_PORTAL (may still be provisioning)"
    fi
fi

# Test 7: Backend connectivity
print_info "Test 7: Backend Web App Connectivity"
WEBAPP_URL="https://$(az webapp show --name "$WEBAPP_NAME" --resource-group "$WEBAPP_RG" --query "defaultHostName" -o tsv 2>/dev/null || echo "pbimcp.azurewebsites.net")"
if curl -s --max-time 10 "$WEBAPP_URL/health" > /dev/null 2>&1; then
    print_status "✅ Backend Web App accessible: $WEBAPP_URL"
else
    print_warning "⚠️  Backend Web App not accessible: $WEBAPP_URL"
fi

# Step 4: Generate comprehensive test report
print_step "Step 4: Generating Test Report"

# Run all tests and capture results
HEALTH_TEST=$(curl -s --max-time 5 "$BASE_URL/health" >/dev/null 2>&1 && echo "PASS" || echo "FAIL")
ROOT_TEST=$(curl -s --max-time 5 "$BASE_URL/" >/dev/null 2>&1 && echo "PASS" || echo "FAIL")
AUTH_TEST=$(test "$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$BASE_URL/mcp/status")" = "401" && echo "PASS" || echo "FAIL")
CORS_TEST=$(curl -s -H "Origin: https://claude.ai" -X OPTIONS "$BASE_URL/health" -D - 2>/dev/null | grep -iq "access-control-allow-origin" && echo "PASS" || echo "FAIL")
BACKEND_TEST=$(curl -s --max-time 5 "$WEBAPP_URL/health" >/dev/null 2>&1 && echo "PASS" || echo "FAIL")

if [ "$OAUTH_AVAILABLE" = true ]; then
    OAUTH_TEST=$(test "$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$AUTH_URL")" = "302" && echo "PASS" || echo "FAIL")
else
    OAUTH_TEST="SKIPPED"
fi

cat > integration_test_report.md << EOF
# 🧪 API Management Integration Test Report

## 📊 Test Summary
- **Test Date**: $(date)
- **Configuration**: Fully automated discovery
- **API Management**: $APIM_NAME
- **Gateway URL**: $GATEWAY_URL
- **API Base URL**: $BASE_URL
- **Backend Web App**: $WEBAPP_URL

## 🧪 Test Results

| Test | Status | Description |
|------|--------|-------------|
| Health Check | **$HEALTH_TEST** | Public health endpoint accessibility |
| Root Endpoint | **$ROOT_TEST** | API root endpoint response |
| Authentication Required | **$AUTH_TEST** | Protected endpoints require authentication |
| CORS Configuration | **$CORS_TEST** | Claude.ai CORS headers present |
| OAuth Authorization | **$OAUTH_TEST** | OAuth flow initiation |
| Backend Connectivity | **$BACKEND_TEST** | Web App backend accessibility |

## 🔗 Configuration URLs

### For Claude.ai Enterprise Integration:
- **Base URL**: \`$BASE_URL\`
- **Authorization URL**: \`$BASE_URL/authorize\`
- **Token URL**: \`https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token\`
- **Client ID**: \`$CLIENT_ID\`
- **Scopes**: \`https://analysis.windows.net/powerbi/api/.default\`

### For App Registration Redirect URIs:
- \`$BASE_URL/auth/callback\`
- \`https://claude.ai/api/mcp/auth_callback\`

## 🎯 Next Steps

### 1. If Tests Pass:
- ✅ Update App Registration redirect URIs (see above)
- ✅ Configure Claude.ai Enterprise with the URLs above
- ✅ Test end-to-end OAuth flow

### 2. If Tests Fail:
- ❌ Health Check FAIL: Check API Management deployment and backend connectivity
- ❌ Authentication FAIL: Verify security policies are applied
- ❌ CORS FAIL: Check API policies include Claude.ai CORS configuration
- ❌ OAuth FAIL: Verify OAuth server configuration and App Registration settings

## 🛠️ Troubleshooting Commands

\`\`\`bash
# Check API Management status
az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME"

# Test backend directly
curl $WEBAPP_URL/health

# Check API operations
az apim api operation list --api-id "powerbi-mcp" --service-name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME"

# Test OAuth URL in browser
echo "OAuth Test URL: $AUTH_URL"
\`\`\`

## 📈 Performance Notes
- Gateway response time: $(curl -s -w "%{time_total}s" --max-time 10 "$BASE_URL/health" -o /dev/null 2>/dev/null || echo "N/A")
- Backend response time: $(curl -s -w "%{time_total}s" --max-time 10 "$WEBAPP_URL/health" -o /dev/null 2>/dev/null || echo "N/A")

---
**Report generated automatically** - No manual configuration required! 🎉
EOF

echo ""
print_status "🎉 Integration Testing Complete!"
print_info "📄 Detailed report saved to: integration_test_report.md"
echo ""

# Show summary
if [ "$HEALTH_TEST" = "PASS" ] && [ "$AUTH_TEST" = "PASS" ] && [ "$CORS_TEST" = "PASS" ]; then
    print_status "🌟 All critical tests PASSED! Your API Management is ready for Claude.ai"
    echo ""
    print_step "🎯 Ready for Claude.ai Integration:"
    echo "  Base URL: $BASE_URL"
    if [ "$OAUTH_AVAILABLE" = true ]; then
        echo "  Authorization URL: $BASE_URL/authorize"
        echo "  Token URL: https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token"
        echo "  Client ID: $CLIENT_ID"
    fi
else
    print_warning "⚠️  Some tests failed - review integration_test_report.md for details"
fi

echo ""
print_info "✨ Fully automated testing complete - no manual configuration needed!"