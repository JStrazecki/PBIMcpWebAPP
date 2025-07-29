#!/bin/bash
# Configure OAuth 2.0 using environment variables from Azure Web App
# This pulls configuration directly from your existing Web App

set -e

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

# Parameters (can be provided or auto-detected)
WEBAPP_NAME=${1:-"pbimcp"}
RESOURCE_GROUP_NAME=${2:-"rg-pbi-mcp-enterprise"}
APIM_NAME=${3}

echo -e "${GREEN}🔧 Configuring OAuth from Azure Web App Environment Variables${NC}"
echo -e "${GREEN}================================================================${NC}"

# Step 1: Get Web App environment variables
print_step "Step 1: Retrieving environment variables from Web App"

if ! az webapp show --name "$WEBAPP_NAME" --resource-group "$(az webapp list --query "[?name=='$WEBAPP_NAME'].resourceGroup" -o tsv)" &> /dev/null; then
    print_error "Web App '$WEBAPP_NAME' not found. Please check the name."
    exit 1
fi

# Get the actual resource group for the web app
WEBAPP_RG=$(az webapp list --query "[?name=='$WEBAPP_NAME'].resourceGroup" -o tsv)
print_info "Found Web App '$WEBAPP_NAME' in resource group '$WEBAPP_RG'"

# Retrieve environment variables
print_info "Retrieving OAuth configuration from Web App..."

TENANT_ID=$(az webapp config appsettings list --name "$WEBAPP_NAME" --resource-group "$WEBAPP_RG" --query "[?name=='AZURE_TENANT_ID'].value" -o tsv)
CLIENT_ID=$(az webapp config appsettings list --name "$WEBAPP_NAME" --resource-group "$WEBAPP_RG" --query "[?name=='AZURE_CLIENT_ID'].value" -o tsv)
CLIENT_SECRET=$(az webapp config appsettings list --name "$WEBAPP_NAME" --resource-group "$WEBAPP_RG" --query "[?name=='AZURE_CLIENT_SECRET'].value" -o tsv)

# Validate retrieved values
if [ -z "$TENANT_ID" ] || [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
    print_error "Missing environment variables in Web App. Required:"
    echo "  - AZURE_TENANT_ID: ${TENANT_ID:-'MISSING'}"
    echo "  - AZURE_CLIENT_ID: ${CLIENT_ID:-'MISSING'}"
    echo "  - AZURE_CLIENT_SECRET: ${CLIENT_SECRET:-'MISSING'}"
    echo ""
    print_info "Please set these environment variables in your Web App:"
    echo "  az webapp config appsettings set --name '$WEBAPP_NAME' --resource-group '$WEBAPP_RG' --settings AZURE_TENANT_ID='your-tenant-id'"
    echo "  az webapp config appsettings set --name '$WEBAPP_NAME' --resource-group '$WEBAPP_RG' --settings AZURE_CLIENT_ID='your-client-id'"
    echo "  az webapp config appsettings set --name '$WEBAPP_NAME' --resource-group '$WEBAPP_RG' --settings AZURE_CLIENT_SECRET='your-client-secret'"
    exit 1
fi

print_status "Retrieved OAuth configuration from Web App"
print_info "Tenant ID: ${TENANT_ID:0:8}..."
print_info "Client ID: ${CLIENT_ID:0:8}..."
print_info "Client Secret: [PROTECTED]"

# Step 2: Auto-detect or get API Management name
if [ -z "$APIM_NAME" ]; then
    print_step "Step 2: Auto-detecting API Management instance"
    APIM_NAME=$(az apim list --resource-group "$RESOURCE_GROUP_NAME" --query "[0].name" -o tsv 2>/dev/null)
    
    if [ -z "$APIM_NAME" ]; then
        print_error "No API Management instance found in resource group '$RESOURCE_GROUP_NAME'"
        print_info "Available API Management instances:"
        az apim list --query "[].{Name:name, ResourceGroup:resourceGroup, Location:location}" -o table
        echo ""
        print_info "Usage: $0 [WEBAPP_NAME] [RESOURCE_GROUP] [APIM_NAME]"
        exit 1
    fi
    
    print_info "Auto-detected API Management: $APIM_NAME"
else
    print_step "Step 2: Using provided API Management: $APIM_NAME"
fi

# Verify API Management exists
if ! az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_error "API Management '$APIM_NAME' not found in resource group '$RESOURCE_GROUP_NAME'"
    exit 1
fi

print_status "API Management instance verified"

# Step 3: Create OAuth 2.0 server in API Management
print_step "Step 3: Configuring OAuth 2.0 server in API Management"

# Check if OAuth server already exists
if az apim authserver show --server-id "microsoft-oauth" --service-name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_info "OAuth server already exists, updating configuration..."
    
    az apim authserver update \
        --server-id "microsoft-oauth" \
        --service-name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --description "Microsoft Azure AD OAuth 2.0 Server (Auto-configured from Web App)" \
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
    print_info "Creating new OAuth server..."
    
    az apim authserver create \
        --server-id "microsoft-oauth" \
        --service-name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --display-name "Microsoft OAuth 2.0" \
        --description "Microsoft Azure AD OAuth 2.0 Server (Auto-configured from Web App)" \
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

print_status "OAuth 2.0 server configured successfully"

# Step 4: Create named values for secure reference
print_step "Step 4: Creating secure named values"

# Store client secret as named value
az apim nv create \
    --service-name "$APIM_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --named-value-id "powerbi-client-secret" \
    --display-name "PowerBI Client Secret" \
    --value "$CLIENT_SECRET" \
    --secret true \
    || print_info "Named value already exists"

# Store tenant ID as named value
az apim nv create \
    --service-name "$APIM_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --named-value-id "powerbi-tenant-id" \
    --display-name "PowerBI Tenant ID" \
    --value "$TENANT_ID" \
    || print_info "Named value already exists"

# Store client ID as named value
az apim nv create \
    --service-name "$APIM_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --named-value-id "powerbi-client-id" \
    --display-name "PowerBI Client ID" \
    --value "$CLIENT_ID" \
    || print_info "Named value already exists"

print_status "Named values created for secure reference"

# Step 5: Get gateway URL and generate configuration
print_step "Step 5: Generating configuration"

GATEWAY_URL=$(az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query "gatewayUrl" -o tsv)

cat > oauth_configuration_summary.json << EOF
{
  "oauth_server_configured": true,
  "source": "Azure Web App Environment Variables",
  "web_app": {
    "name": "$WEBAPP_NAME",
    "resource_group": "$WEBAPP_RG"
  },
  "api_management": {
    "name": "$APIM_NAME",
    "resource_group": "$RESOURCE_GROUP_NAME",
    "gateway_url": "$GATEWAY_URL"
  },
  "oauth_configuration": {
    "tenant_id": "$TENANT_ID",
    "client_id": "$CLIENT_ID",
    "authorization_endpoint": "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/authorize",
    "token_endpoint": "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token",
    "scopes": ["https://analysis.windows.net/powerbi/api/.default"]
  },
  "claude_integration": {
    "base_url": "$GATEWAY_URL/powerbi-mcp",
    "authorization_url": "$GATEWAY_URL/powerbi-mcp/authorize",
    "callback_url": "$GATEWAY_URL/powerbi-mcp/auth/callback"
  }
}
EOF

echo -e "${GREEN}🎉 OAuth Configuration Complete!${NC}"
echo -e "${GREEN}=================================${NC}"
print_info "Configuration source: Web App '$WEBAPP_NAME'"
print_info "API Management: '$APIM_NAME'"
print_info "Gateway URL: $GATEWAY_URL"
echo ""
print_info "📄 Configuration saved to: oauth_configuration_summary.json"
echo ""
print_step "Next Steps:"
echo "1. Run: ./create_mcp_api.sh (if not done already)"
echo "2. Run: ./apply_policies.sh"
echo "3. Update App Registration redirect URIs:"
echo "   - $GATEWAY_URL/powerbi-mcp/auth/callback"
echo "   - https://claude.ai/api/mcp/auth_callback"