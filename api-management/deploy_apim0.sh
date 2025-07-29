#!/bin/bash
# Deploy API Management - MANUAL CONFIGURATION REQUIRED
# Edit the variables below before running

set -e

# 🔧 MANUAL CONFIGURATION - EDIT THESE VALUES
RESOURCE_GROUP_NAME="rg-pbi-mcp-enterprise"  # Edit if needed
APIM_NAME="pbi-mcp-apim-$(date +%s)"        # Edit to use fixed name if preferred
LOCATION="East US"                           # Edit for your preferred region
SKU="Developer"                              # Options: Developer, Basic, Standard, Premium
PUBLISHER_EMAIL="admin@company.com"          # Edit with your email
PUBLISHER_NAME="PowerBI MCP Enterprise"      # Edit organization name

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

echo -e "${GREEN}🚀 API Management Deployment (Manual Configuration)${NC}"
echo -e "${GREEN}================================================${NC}"

print_info "Configuration:"
print_info "Resource Group: $RESOURCE_GROUP_NAME"
print_info "APIM Name: $APIM_NAME"
print_info "Location: $LOCATION"
print_info "SKU: $SKU"

# Verify Azure CLI
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed"
    exit 1
fi

if ! az account show &> /dev/null; then
    print_info "Please login to Azure..."
    az login
fi

# Create Resource Group
print_step "Creating Resource Group"
if az group show --name "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_status "Resource group already exists"
else
    az group create --name "$RESOURCE_GROUP_NAME" --location "$LOCATION"
    print_status "Resource group created"
fi

# Deploy API Management
print_step "Deploying API Management (15-30 minutes)"
if az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_status "API Management already exists"
else
    print_info "⏳ This will take 15-30 minutes..."
    az apim create \
        --name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --location "$LOCATION" \
        --sku-name "$SKU" \
        --sku-capacity 1 \
        --publisher-email "$PUBLISHER_EMAIL" \
        --publisher-name "$PUBLISHER_NAME" \
        --no-wait
    
    print_info "Waiting for deployment..."
    az apim wait --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" --created --timeout 2400
    print_status "API Management deployed successfully"
fi

# Get gateway URL
GATEWAY_URL=$(az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query "gatewayUrl" -o tsv)

# Save configuration for next scripts
cat > apim_config.txt << EOF
RESOURCE_GROUP_NAME=$RESOURCE_GROUP_NAME
APIM_NAME=$APIM_NAME
GATEWAY_URL=$GATEWAY_URL
EOF

echo ""
print_status "🎉 API Management Deployment Complete!"
print_info "Gateway URL: $GATEWAY_URL"
print_info "Configuration saved to: apim_config.txt"
echo ""
print_step "Next Steps:"
echo "1. Edit and run: ./configure_oauth0.sh"
echo "2. Edit and run: ./create_api0.sh"
echo "3. Edit and run: ./apply_policies0.sh"