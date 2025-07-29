#!/bin/bash
# Configure OAuth 2.0 Server - MANUAL CONFIGURATION REQUIRED
# Edit the variables below before running

set -e

# 🔧 MANUAL CONFIGURATION - EDIT THESE VALUES
TENANT_ID="your-tenant-id"                           # Azure Portal → App Registrations → Overview → Directory (tenant) ID
CLIENT_ID="5bdb10bc-bb29-4af9-8cb5-062690e6be15"     # Azure Portal → App Registrations → Overview → Application (client) ID  
CLIENT_SECRET="your-client-secret"                    # Azure Portal → App Registrations → Certificates & secrets → Client secrets

# Try to load APIM config from previous script
if [ -f "apim_config.txt" ]; then
    source apim_config.txt
    echo "✅ Loaded APIM configuration from apim_config.txt"
else
    # Manual fallback if config file not found
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

echo -e "${GREEN}🔧 OAuth 2.0 Configuration (Manual Setup)${NC}"
echo -e "${GREEN}=========================================${NC}"

# Validate required variables
if [ "$TENANT_ID" = "your-tenant-id" ] || [ "$CLIENT_SECRET" = "your-client-secret" ]; then
    print_error "Please edit this script and set the required values:"
    echo "  TENANT_ID: Currently '$TENANT_ID'"
    echo "  CLIENT_ID: Currently '$CLIENT_ID'"
    echo "  CLIENT_SECRET: Currently '$CLIENT_SECRET'"
    echo ""
    print_info "Get these values from Azure Portal → App Registrations → Your App"
    exit 1
fi

print_info "Configuration:"
print_info "Tenant ID: ${TENANT_ID:0:8}..."
print_info "Client ID: ${CLIENT_ID:0:8}..."
print_info "APIM Name: $APIM_NAME"

# Verify API Management exists
if ! az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_error "API Management '$APIM_NAME' not found in resource group '$RESOURCE_GROUP_NAME'"
    print_info "Available API Management instances:"
    az apim list --query "[].{Name:name, ResourceGroup:resourceGroup}" -o table
    exit 1
fi

# Configure OAuth server
print_step "Configuring OAuth 2.0 Server"

if az apim authserver show --server-id "microsoft-oauth" --service-name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_info "Updating existing OAuth server..."
    az apim authserver update \
        --server-id "microsoft-oauth" \
        --service-name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --description "Microsoft Azure AD OAuth 2.0 Server (Manual Configuration)" \
        --authorization-endpoint "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/authorize" \
        --token-endpoint "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token" \
        --client-id "$CLIENT_ID" \
        --client-secret "$CLIENT_SECRET" \
        --authorization-methods "GET" "POST" \
        --grant-types "authorization_code" "client_credentials" \
        --client-authentication-method "Basic" \
        --default-scope "https://analysis.windows.net/powerbi/api/.default" \
        --support-state true
else
    print_info "Creating OAuth server..."
    az apim authserver create \
        --server-id "microsoft-oauth" \
        --service-name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --display-name "Microsoft OAuth 2.0" \
        --description "Microsoft Azure AD OAuth 2.0 Server (Manual Configuration)" \
        --authorization-endpoint "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/authorize" \
        --token-endpoint "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token" \
        --client-id "$CLIENT_ID" \
        --client-secret "$CLIENT_SECRET" \
        --authorization-methods "GET" "POST" \
        --grant-types "authorization_code" "client_credentials" \
        --client-authentication-method "Basic" \
        --default-scope "https://analysis.windows.net/powerbi/api/.default" \
        --support-state true
fi

# Create named values for secure storage
print_step "Creating Named Values for Security"

az apim nv create \
    --service-name "$APIM_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --named-value-id "powerbi-client-secret" \
    --display-name "PowerBI Client Secret" \
    --value "$CLIENT_SECRET" \
    --secret true \
    2>/dev/null || print_info "Named value already exists"

az apim nv create \
    --service-name "$APIM_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --named-value-id "powerbi-tenant-id" \
    --display-name "PowerBI Tenant ID" \
    --value "$TENANT_ID" \
    2>/dev/null || print_info "Named value already exists"

# Save OAuth config for next scripts
cat > oauth_config.txt << EOF
TENANT_ID=$TENANT_ID
CLIENT_ID=$CLIENT_ID
CLIENT_SECRET=$CLIENT_SECRET
EOF

echo ""
print_status "🎉 OAuth Configuration Complete!"
print_info "Configuration saved to: oauth_config.txt"
echo ""
print_step "Next Steps:"
echo "1. Edit and run: ./create_api0.sh"
echo "2. Edit and run: ./apply_policies0.sh"