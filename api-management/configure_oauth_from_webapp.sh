#!/bin/bash
# Configure OAuth from Web App Environment Variables - NO MANUAL CONFIGURATION
# Automatically pulls configuration from your Azure Web App

set -e

# Auto-detect parameters
WEBAPP_NAME=${1:-"pbimcp"}
RESOURCE_GROUP_NAME=${2:-"rg-pbi-mcp-enterprise"}
APIM_NAME=${3}

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

echo -e "${GREEN}🔧 OAuth Configuration from Web App (Fully Automated)${NC}"
echo -e "${GREEN}==================================================${NC}"

# Step 1: Find and validate Web App
print_step "Step 1: Locating Web App and Configuration"

# Find the web app's resource group
WEBAPP_RG=$(az webapp list --query "[?name=='$WEBAPP_NAME'].resourceGroup" -o tsv | head -1)
if [ -z "$WEBAPP_RG" ]; then
    print_error "Web App '$WEBAPP_NAME' not found"
    print_info "Available Web Apps:"
    az webapp list --query "[].{Name:name, ResourceGroup:resourceGroup}" -o table
    exit 1
fi

print_status "Found Web App '$WEBAPP_NAME' in resource group '$WEBAPP_RG'"

# Get OAuth configuration from Web App
TENANT_ID=$(az webapp config appsettings list --name "$WEBAPP_NAME" --resource-group "$WEBAPP_RG" --query "[?name=='AZURE_TENANT_ID'].value" -o tsv)
CLIENT_ID=$(az webapp config appsettings list --name "$WEBAPP_NAME" --resource-group "$WEBAPP_RG" --query "[?name=='AZURE_CLIENT_ID'].value" -o tsv)
CLIENT_SECRET=$(az webapp config appsettings list --name "$WEBAPP_NAME" --resource-group "$WEBAPP_RG" --query "[?name=='AZURE_CLIENT_SECRET'].value" -o tsv)

# Validate OAuth configuration
if [ -z "$TENANT_ID" ] || [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
    print_error "Missing OAuth configuration in Web App environment variables"
    echo ""
    print_info "Required environment variables in Web App '$WEBAPP_NAME':"
    echo "  AZURE_TENANT_ID: ${TENANT_ID:-'❌ MISSING'}"
    echo "  AZURE_CLIENT_ID: ${CLIENT_ID:-'❌ MISSING'}"
    echo "  AZURE_CLIENT_SECRET: ${CLIENT_SECRET:-'❌ MISSING'}"
    echo ""
    print_info "Set these using:"
    echo "  az webapp config appsettings set --name '$WEBAPP_NAME' --resource-group '$WEBAPP_RG' \\"
    echo "    --settings AZURE_TENANT_ID='your-tenant-id' \\"
    echo "               AZURE_CLIENT_ID='your-client-id' \\"
    echo "               AZURE_CLIENT_SECRET='your-client-secret'"
    exit 1
fi

print_status "OAuth configuration retrieved from Web App"
print_info "✅ Tenant ID: ${TENANT_ID:0:8}..."
print_info "✅ Client ID: ${CLIENT_ID:0:8}..."
print_info "✅ Client Secret: [SECURED]"

# Step 2: Auto-detect or get API Management name
if [ -z "$APIM_NAME" ]; then
    print_step "Step 2: Auto-detecting API Management instance"
    APIM_NAME=$(az apim list --resource-group "$RESOURCE_GROUP_NAME" --query "[0].name" -o tsv 2>/dev/null)
    
    if [ -z "$APIM_NAME" ]; then
        print_error "No API Management instance found in resource group '$RESOURCE_GROUP_NAME'"
        print_info "Available API Management instances:"
        az apim list --query "[].{Name:name, ResourceGroup:resourceGroup, Location:location}" -o table
        exit 1
    fi
    
    print_status "Auto-detected API Management: $APIM_NAME"
else
    print_step "Step 2: Using provided API Management: $APIM_NAME"
fi

# Verify API Management exists
if ! az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_error "API Management '$APIM_NAME' not found in resource group '$RESOURCE_GROUP_NAME'"
    exit 1
fi

print_status "API Management instance verified"

# Step 3: Configure OAuth 2.0 server
print_step "Step 3: Configuring OAuth 2.0 Server"

if az apim authserver show --server-id "microsoft-oauth" --service-name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
    print_info "Updating existing OAuth server..."
    az apim authserver update \
        --server-id "microsoft-oauth" \
        --service-name "$APIM_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --description "Microsoft Azure AD OAuth 2.0 (Auto-configured from Web App)" \
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
        --description "Microsoft Azure AD OAuth 2.0 (Auto-configured from Web App)" \
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
print_step "Step 4: Creating Named Values for Security"

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

az apim nv create \
    --service-name "$APIM_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --named-value-id "powerbi-client-id" \
    --display-name "PowerBI Client ID" \
    --value "$CLIENT_ID" \
    2>/dev/null || print_info "Named value already exists"

print_status "Named values created for secure reference"

# Step 5: Get gateway URL and generate configuration  
print_step "Step 5: Generating Configuration Summary"

GATEWAY_URL=$(az apim show --name "$APIM_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query "gatewayUrl" -o tsv)

cat > oauth_configuration_summary.json << EOF
{
  "configuration_source": "Azure Web App Environment Variables",
  "auto_configured": true,
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
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
  "claude_integration_urls": {
    "base_url": "$GATEWAY_URL/powerbi-mcp",
    "authorization_url": "$GATEWAY_URL/powerbi-mcp/authorize",
    "callback_url": "$GATEWAY_URL/powerbi-mcp/auth/callback"
  }
}
EOF

echo ""
print_status "🎉 OAuth Configuration Complete (Fully Automated)!"
print_info "📄 Configuration saved to: oauth_configuration_summary.json"
print_info "🌐 Gateway URL: $GATEWAY_URL"
print_info "🔐 OAuth Server: microsoft-oauth"
echo ""
print_step "🎯 Next Steps:"
echo "1. Run API creation: ./create_api0.sh (edit APIM name first)"
echo "2. Run security policies: ./apply_policies0.sh"
echo "3. Update App Registration redirect URIs:"
echo "   - $GATEWAY_URL/powerbi-mcp/auth/callback"
echo "   - https://claude.ai/api/mcp/auth_callback"
echo ""
print_info "✨ No manual OAuth configuration required - everything auto-detected from Web App!"