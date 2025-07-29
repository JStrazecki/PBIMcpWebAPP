#!/bin/bash
# Test API Management Integration - MANUAL CONFIGURATION REQUIRED  
# Edit the variables below before running

set -e

# Try to load configuration from previous scripts
if [ -f "apim_config.txt" ]; then
    source apim_config.txt
    echo "✅ Loaded APIM configuration"
fi

if [ -f "oauth_config.txt" ]; then
    source oauth_config.txt
    echo "✅ Loaded OAuth configuration"  
fi

if [ -f "api_config.txt" ]; then
    source api_config.txt
    echo "✅ Loaded API configuration"
fi

# 🔧 MANUAL CONFIGURATION - EDIT IF CONFIG FILES NOT FOUND
if [ -z "$GATEWAY_URL" ]; then
    GATEWAY_URL="https://your-apim-gateway.azure-api.net"  # Edit with your actual gateway URL
    API_PATH="powerbi-mcp"                                 # Edit if different
    TENANT_ID="your-tenant-id"                             # Edit if oauth_config.txt not found
    CLIENT_ID="5bdb10bc-bb29-4af9-8cb5-062690e6be15"       # Edit if oauth_config.txt not found
fi

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

echo -e "${GREEN}🧪 API Management Integration Testing${NC}"
echo -e "${GREEN}====================================${NC}"

# Validate configuration
if [ "$GATEWAY_URL" = "https://your-apim-gateway.azure-api.net" ] || [ "$TENANT_ID" = "your-tenant-id" ]; then
    print_error "Please edit this script or ensure config files exist with correct values:"
    echo "  GATEWAY_URL: $GATEWAY_URL"
    echo "  TENANT_ID: $TENANT_ID"
    echo "  CLIENT_ID: $CLIENT_ID"
    exit 1
fi

BASE_URL="$GATEWAY_URL/$API_PATH"

print_info "Testing Configuration:"
print_info "Gateway URL: $GATEWAY_URL"
print_info "API Base URL: $BASE_URL"
print_info "Tenant ID: ${TENANT_ID:0:8}..."

# Test 1: Health Check (no authentication required)
print_step "Test 1: Health Check Endpoint"
if curl -s --max-time 10 "$BASE_URL/health" > /dev/null 2>&1; then
    print_status "Health endpoint accessible"
    
    # Get health response  
    HEALTH_RESPONSE=$(curl -s --max-time 10 "$BASE_URL/health")
    if echo "$HEALTH_RESPONSE" | grep -q "healthy\\|status\\|service"; then
        print_status "Health endpoint returns valid response"
    else
        print_warning "Health endpoint responds but content may be unexpected"
    fi
else
    print_error "Health endpoint not accessible"
fi

# Test 2: Root endpoint
print_step "Test 2: Root Endpoint"
if curl -s --max-time 10 "$BASE_URL/" > /dev/null 2>&1; then
    print_status "Root endpoint accessible"
else
    print_warning "Root endpoint not accessible (may be expected)"
fi

# Test 3: Protected endpoint (should return 401)
print_step "Test 3: Protected Endpoint (Should Require Authentication)"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$BASE_URL/mcp/status")
if [ "$HTTP_STATUS" = "401" ]; then
    print_status "Protected endpoint correctly requires authentication (401)"
elif [ "$HTTP_STATUS" = "200" ]; then
    print_warning "Protected endpoint accessible without authentication (security concern)"
else
    print_info "Protected endpoint returned status: $HTTP_STATUS"
fi

# Test 4: CORS Headers
print_step "Test 4: CORS Configuration"
CORS_RESPONSE=$(curl -s -H "Origin: https://claude.ai" -H "Access-Control-Request-Method: GET" -X OPTIONS "$BASE_URL/health" -D -)
if echo "$CORS_RESPONSE" | grep -iq "access-control-allow-origin"; then
    print_status "CORS headers present"
else
    print_warning "CORS headers not detected"
fi

# Test 5: OAuth Authorization URL
print_step "Test 5: OAuth Authorization Endpoint"
AUTH_URL="$BASE_URL/authorize?response_type=code&client_id=$CLIENT_ID&redirect_uri=https://claude.ai/api/mcp/auth_callback&scope=https://analysis.windows.net/powerbi/api/.default"

if curl -s -I --max-time 10 "$AUTH_URL" | grep -q "302\\|Location"; then
    print_status "OAuth authorization endpoint redirects correctly"
else
    print_warning "OAuth authorization endpoint may not be configured correctly"
fi

# Test 6: API Management Developer Portal
print_step "Test 6: Developer Portal Accessibility"
if [[ "$GATEWAY_URL" =~ https://([^.]+)\.azure-api\.net ]]; then
    APIM_NAME="${BASH_REMATCH[1]}"
    DEVELOPER_PORTAL="https://$APIM_NAME.developer.azure-api.net"
    
    if curl -s --max-time 10 "$DEVELOPER_PORTAL" > /dev/null 2>&1; then
        print_status "Developer portal accessible: $DEVELOPER_PORTAL"
    else
        print_info "Developer portal: $DEVELOPER_PORTAL (may take time to provision)"
    fi
fi

# Test 7: Backend connectivity
print_step "Test 7: Backend Web App Connectivity"
if [ -n "$BACKEND_URL" ]; then
    if curl -s --max-time 10 "$BACKEND_URL/health" > /dev/null 2>&1; then
        print_status "Backend Web App accessible"
    else
        print_warning "Backend Web App not accessible (check $BACKEND_URL)"
    fi
else
    print_info "Backend URL not configured in test"
fi

# Generate test report
print_step "Generating Test Report"
cat > integration_test_report.txt << EOF
API Management Integration Test Report
======================================
Test Date: $(date)
Gateway URL: $GATEWAY_URL
API Base URL: $BASE_URL

Test Results:
1. Health Check: $(curl -s --max-time 5 "$BASE_URL/health" >/dev/null 2>&1 && echo "PASS" || echo "FAIL")
2. Root Endpoint: $(curl -s --max-time 5 "$BASE_URL/" >/dev/null 2>&1 && echo "PASS" || echo "FAIL")  
3. Authentication Required: $(test "$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$BASE_URL/mcp/status")" = "401" && echo "PASS" || echo "FAIL")
4. CORS Headers: $(curl -s -H "Origin: https://claude.ai" -X OPTIONS "$BASE_URL/health" -D - | grep -iq "access-control-allow-origin" && echo "PASS" || echo "FAIL")
5. OAuth Redirect: $(curl -s -I --max-time 5 "$AUTH_URL" | grep -q "302\\|Location" && echo "PASS" || echo "FAIL")

Next Steps:
1. Update App Registration redirect URIs:
   - $BASE_URL/auth/callback
   - https://claude.ai/api/mcp/auth_callback

2. Configure Claude.ai Enterprise:
   - Base URL: $BASE_URL
   - Authorization URL: $BASE_URL/authorize
   - Token URL: https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token
   - Client ID: $CLIENT_ID
   - Scopes: https://analysis.windows.net/powerbi/api/.default

3. Test OAuth Flow:
   Visit: $AUTH_URL
EOF

echo ""
print_status "🎉 Integration Testing Complete!"
print_info "Test report saved to: integration_test_report.txt"
echo ""
print_step "Summary URLs for Claude.ai Configuration:"
echo "  Base URL: $BASE_URL"
echo "  Authorization URL: $BASE_URL/authorize"
echo "  OAuth Test URL: $AUTH_URL"
echo ""
print_step "Next Steps:"
echo "1. Review integration_test_report.txt"
echo "2. Update App Registration redirect URIs"
echo "3. Configure Claude.ai Enterprise"
echo "4. Test end-to-end OAuth flow"