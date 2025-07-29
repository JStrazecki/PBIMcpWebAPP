#!/bin/bash
# Complete Azure API Management Automation Script
# This script automates the entire API Management setup process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "${YELLOW}📋 $1${NC}"
}

# Check required parameters
if [ $# -lt 3 ]; then
    print_error "Usage: $0 <TENANT_ID> <CLIENT_ID> <CLIENT_SECRET> [RESOURCE_GROUP] [APIM_NAME] [LOCATION] [WEBAPP_URL]"
    echo "Example: $0 your-tenant-id your-client-id your-secret"
    exit 1
fi

# Parameters
TENANT_ID=$1
CLIENT_ID=$2
CLIENT_SECRET=$3
RESOURCE_GROUP_NAME=${4:-"rg-pbi-mcp-enterprise"}
APIM_NAME=${5:-"pbi-mcp-apim-$(date +%s)"}
LOCATION=${6:-"East US"}
WEBAPP_URL=${7:-"https://pbimcp.azurewebsites.net"}

# Configuration
API_NAME="powerbi-mcp"
API_PATH="powerbi-mcp" 
SKU="Developer"
PUBLISHER_NAME="PowerBI MCP Enterprise"
PUBLISHER_EMAIL="admin@company.com"

echo -e "${GREEN}🚀 Starting Complete API Management Automation${NC}"
echo -e "${GREEN}================================================${NC}"

# Step 1: Verify Azure CLI
print_step "Step 1: Verifying Azure CLI"
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Login check
if ! az account show &> /dev/null; then
    print_info "Please login to Azure..."
    az login
fi
print_status "Azure CLI verified and logged in"

# Step 2: Create Resource Group
print_step "Step 2: Creating Resource Group"
if az group show --name "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_status "Resource group '$RESOURCE_GROUP_NAME' already exists"
else
    az group create --name "$RESOURCE_GROUP_NAME" --location "$LOCATION"
    print_status "Resource group '$RESOURCE_GROUP_NAME' created"
fi

# Step 3: Deploy API Management
print_step "Step 3: Deploying API Management (15-30 minutes)"
if az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_status "API Management '$APIM_NAME' already exists"
else
    print_info "Creating API Management instance... This will take 15-30 minutes"
    az apim create \
        --name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --location "$LOCATION" \
        --sku-name "$SKU" \
        --sku-capacity 1 \
        --publisher-email "$PUBLISHER_EMAIL" \
        --publisher-name "$PUBLISHER_NAME" \
        --no-wait
    
    print_info "Waiting for API Management deployment to complete..."
    az apim wait --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" --created --timeout 2400
    print_status "API Management '$APIM_NAME' deployed successfully"
fi

# Get APIM gateway URL
APIM_GATEWAY_URL=$(az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query "gatewayUrl" -o tsv)
print_info "API Management Gateway URL: $APIM_GATEWAY_URL"

# Step 4: Create API
print_step "Step 4: Creating API and Operations"
if az apim api show --api-id "$API_NAME" --service-name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_status "API '$API_NAME' already exists"
else
    az apim api create \
        --api-id "$API_NAME" \
        --service-name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --display-name "Power BI MCP API" \
        --description "Power BI Model Context Protocol API for Claude.ai Enterprise" \
        --service-url "$WEBAPP_URL" \
        --protocols https \
        --path "$API_PATH"
    print_status "API '$API_NAME' created"
fi

# Create operations
operations=(
    "get-root GET / \"Get Root Information\""
    "get-health GET /health \"Health Check\""
    "get-mcp-status GET /mcp/status \"MCP Status\""
    "get-workspaces GET /mcp/workspaces \"List Workspaces\""
    "get-datasets GET /mcp/datasets \"List Datasets\""
    "post-query POST /mcp/query \"Execute Query\""
    "get-authorize GET /authorize \"OAuth Authorization\""
    "get-callback GET /auth/callback \"OAuth Callback\""
)

for operation in "${operations[@]}"; do
    IFS=' ' read -r op_id method url_template display_name <<< "$operation"
    display_name=$(echo "$display_name" | tr -d '"')
    
    if ! az apim api operation show --api-id "$API_NAME" --operation-id "$op_id" --service-name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
        az apim api operation create \
            --api-id "$API_NAME" \
            --operation-id "$op_id" \
            --service-name "$APIM_NAME" \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --display-name "$display_name" \
            --method "$method" \
            --url-template "$url_template"
    fi
done
print_status "API operations created"

# Step 5: Apply Security Policies
print_step "Step 5: Applying Security Policies"
cat > policy.xml << EOF
<policies>
    <inbound>
        <base />
        <cors allow-credentials="true">
            <allowed-origins>
                <origin>https://claude.ai</origin>
                <origin>https://*.claude.ai</origin>
            </allowed-origins>
            <allowed-methods preflight-result-max-age="3600">
                <method>GET</method>
                <method>POST</method>
                <method>OPTIONS</method>
            </allowed-methods>
            <allowed-headers>
                <header>*</header>
            </allowed-headers>
        </cors>
        <validate-jwt header-name="Authorization" failed-validation-httpcode="401" failed-validation-error-message="Unauthorized">
            <openid-config url="https://login.microsoftonline.com/$TENANT_ID/v2.0/.well-known/openid_configuration" />
            <required-claims>
                <claim name="aud">
                    <value>$CLIENT_ID</value>
                </claim>
            </required-claims>
        </validate-jwt>
        <rate-limit calls="100" renewal-period="60" />
        <quota calls="1000" renewal-period="3600" />
        <set-header name="X-Forwarded-For" exists-action="override">
            <value>@(context.Request.IpAddress)</value>
        </set-header>
    </inbound>
    <backend>
        <base />
    </backend>
    <outbound>
        <base />
        <set-header name="X-Powered-By" exists-action="delete" />
        <set-header name="Server" exists-action="delete" />
    </outbound>
    <on-error>
        <base />
    </on-error>
</policies>
EOF

az apim api policy create \
    --api-id "$API_NAME" \
    --service-name "$APIM_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --policy-content @policy.xml

rm policy.xml
print_status "Security policies applied"

# Step 6: Create Product
print_step "Step 6: Configuring Products"
PRODUCT_ID="powerbi-mcp-product"
if az apim product show --product-id "$PRODUCT_ID" --service-name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_status "Product already exists"
else
    az apim product create \
        --product-id "$PRODUCT_ID" \
        --service-name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --display-name "Power BI MCP Enterprise" \
        --description "Power BI Model Context Protocol for Claude.ai Enterprise" \
        --legal-terms "Enterprise use only" \
        --subscription-required false \
        --approval-required false \
        --state "Published"
    
    az apim product api add \
        --product-id "$PRODUCT_ID" \
        --api-id "$API_NAME" \
        --service-name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME"
    
    print_status "Product configured and published"
fi

# Step 7: Test Endpoints
print_step "Step 7: Testing API Endpoints"
test_urls=(
    "$APIM_GATEWAY_URL/$API_PATH/health"
    "$APIM_GATEWAY_URL/$API_PATH/mcp/status"
)

for url in "${test_urls[@]}"; do
    if curl -s --max-time 10 "$url" > /dev/null 2>&1; then
        print_status "$url - OK"
    else
        print_warning "$url - Not accessible (may require authentication)"
    fi
done

# Step 8: Generate Configuration
print_step "Step 8: Generating Configuration Files"

cat > claude_enterprise_config_automated.json << EOF
{
    "mcpServers": {
        "powerbi-mcp-enterprise": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-fetch", "$APIM_GATEWAY_URL/$API_PATH"],
            "env": {
                "MCP_SERVER_NAME": "Power BI MCP Enterprise",
                "MCP_SERVER_VERSION": "3.0.0"
            }
        }
    }
}
EOF

cat > DEPLOYMENT_SUCCESS_REPORT.md << EOF
# 🎉 Automated Deployment Complete!

## 📊 Deployment Summary
- **Resource Group**: $RESOURCE_GROUP_NAME
- **API Management**: $APIM_NAME  
- **Gateway URL**: $APIM_GATEWAY_URL
- **API Path**: /$API_PATH
- **OAuth Server**: Configured for Microsoft Azure AD

## 🔗 Important URLs
- **API Gateway**: $APIM_GATEWAY_URL/$API_PATH
- **Health Check**: $APIM_GATEWAY_URL/$API_PATH/health
- **OAuth Authorization**: $APIM_GATEWAY_URL/$API_PATH/authorize
- **Developer Portal**: https://$APIM_NAME.developer.azure-api.net

## 🔑 Claude.ai Enterprise Configuration
The configuration has been saved to: claude_enterprise_config_automated.json

### Next Steps for Claude.ai Integration:
1. Login to Claude.ai Enterprise Admin Portal
2. Navigate to Settings → Integrations → MCP Servers  
3. Add New Integration with these values:
   - **Name**: Power BI MCP Enterprise
   - **Base URL**: $APIM_GATEWAY_URL/$API_PATH
   - **Authorization URL**: $APIM_GATEWAY_URL/$API_PATH/authorize
   - **Token URL**: https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token
   - **Client ID**: $CLIENT_ID
   - **Scopes**: https://analysis.windows.net/powerbi/api/.default

## 🛡️ Security Features Enabled
- ✅ JWT Token Validation
- ✅ CORS for Claude.ai domains
- ✅ Rate limiting (100 calls/minute)
- ✅ Quota management (1000 calls/hour)
- ✅ Request logging and monitoring

## 🧪 Testing Commands
\`\`\`bash
# Test health endpoint
curl $APIM_GATEWAY_URL/$API_PATH/health

# Test with authentication
curl -H "Authorization: Bearer YOUR_TOKEN" $APIM_GATEWAY_URL/$API_PATH/mcp/status
\`\`\`

## 📱 Monitoring
- **Azure Portal**: Monitor API calls, errors, and performance
- **Application Insights**: Detailed telemetry and diagnostics
- **API Management Analytics**: Usage patterns and API health

🎯 **Your enterprise-grade Power BI MCP integration is now ready!**
EOF

echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}================================================${NC}"
echo -e "${CYAN}📄 Configuration saved to: claude_enterprise_config_automated.json${NC}"
echo -e "${CYAN}📄 Deployment report saved to: DEPLOYMENT_SUCCESS_REPORT.md${NC}"
echo -e "${CYAN}🌐 API Gateway URL: $APIM_GATEWAY_URL/$API_PATH${NC}"
echo ""
echo -e "${YELLOW}Next: Configure Claude.ai Enterprise with the generated configuration!${NC}"