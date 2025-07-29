#!/bin/bash
# Create MCP API - MANUAL CONFIGURATION REQUIRED
# Edit the variables below before running

set -e

# 🔧 MANUAL CONFIGURATION - EDIT THESE VALUES
BACKEND_URL="https://pbimcp.azurewebsites.net"       # Your Web App URL
API_NAME="powerbi-mcp"                               # API identifier (no spaces)
API_PATH="powerbi-mcp"                               # URL path for API
API_DISPLAY_NAME="Power BI MCP API"                  # Display name in portal

# Try to load configuration from previous scripts
if [ -f "apim_config.txt" ]; then
    source apim_config.txt
    echo "✅ Loaded APIM configuration"
else
    # Manual fallback
    RESOURCE_GROUP_NAME="rg-pbi-mcp-enterprise"      # Edit if different
    APIM_NAME="your-apim-name"                        # Edit with your APIM name
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_step() { echo -e "${YELLOW}📋 $1${NC}"; }

echo -e "${GREEN}🔧 API Creation (Manual Configuration)${NC}"
echo -e "${GREEN}====================================${NC}"

# Validate configuration
if [ "$APIM_NAME" = "your-apim-name" ]; then
    print_error "Please edit this script and set APIM_NAME to your actual API Management name"
    exit 1
fi

print_info "Configuration:"
print_info "APIM Name: $APIM_NAME"
print_info "Backend URL: $BACKEND_URL"
print_info "API Name: $API_NAME"
print_info "API Path: $API_PATH"

# Verify API Management exists
if ! az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_error "API Management '$APIM_NAME' not found"
    exit 1
fi

# Create API
print_step "Creating Power BI MCP API"
if az apim api show --api-id "$API_NAME" --service-name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_status "API already exists"
else
    az apim api create \
        --api-id "$API_NAME" \
        --service-name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --display-name "$API_DISPLAY_NAME" \
        --description "Power BI Model Context Protocol API for Claude.ai Enterprise" \
        --service-url "$BACKEND_URL" \
        --protocols https \
        --path "$API_PATH"
    print_status "API created"
fi

# Create all required operations
print_step "Creating API Operations"
operations=(
    "get-root GET / \"Get Root Information\""
    "get-health GET /health \"Health Check\""
    "get-mcp-status GET /mcp/status \"MCP Status\""
    "get-workspaces GET /mcp/workspaces \"List Power BI Workspaces\""
    "get-datasets GET /mcp/datasets \"List Power BI Datasets\""
    "post-query POST /mcp/query \"Execute Power BI Query\""
    "get-authorize GET /authorize \"OAuth Authorization Endpoint\""
    "get-callback GET /auth/callback \"OAuth Callback Endpoint\""
)

for operation in "${operations[@]}"; do
    IFS=' ' read -r op_id method url_template display_name <<< "$operation"
    display_name=$(echo "$display_name" | tr -d '"')
    
    if az apim api operation show --api-id "$API_NAME" --operation-id "$op_id" --service-name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
        print_info "Operation $op_id already exists"
    else
        az apim api operation create \
            --api-id "$API_NAME" \
            --operation-id "$op_id" \
            --service-name "$APIM_NAME" \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --display-name "$display_name" \
            --method "$method" \
            --url-template "$url_template"
        print_info "Created operation: $display_name"
    fi
done

# Create Product
print_step "Creating Product"
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
    
    # Add API to Product
    az apim product api add \
        --product-id "$PRODUCT_ID" \
        --api-id "$API_NAME" \
        --service-name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME"
    
    print_status "Product created and API added"
fi

# Save API config for next scripts
cat > api_config.txt << EOF
API_NAME=$API_NAME
API_PATH=$API_PATH
BACKEND_URL=$BACKEND_URL
EOF

echo ""
print_status "🎉 API Creation Complete!"
print_info "Configuration saved to: api_config.txt"
echo ""
print_step "Next Steps:"
echo "1. Edit and run: ./apply_policies0.sh"
echo "2. Edit and run: ./test_integration0.sh"