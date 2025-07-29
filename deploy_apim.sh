#!/bin/bash
# Azure API Management Deployment Script for Power BI MCP Server

echo "🚀 Deploying Azure API Management for Power BI MCP Server..."

# Configuration variables
RESOURCE_GROUP="rg-pbi-mcp-enterprise"
LOCATION="eastus"
APIM_NAME="pbi-mcp-apim-$(date +%s)"  # Add timestamp to ensure uniqueness
PUBLISHER_EMAIL="admin@company.com"  # Replace with your email
PUBLISHER_NAME="Power BI MCP Enterprise"
SKU="Developer"  # Use "Standard" or "Premium" for production

echo "📋 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  APIM Name: $APIM_NAME"
echo "  SKU: $SKU"
echo ""

# Create resource group
echo "🏗️  Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output table

if [ $? -ne 0 ]; then
    echo "❌ Failed to create resource group"
    exit 1
fi

# Create API Management instance
echo "🔧 Creating API Management instance (this takes 15-30 minutes)..."
echo "⏰ Started at: $(date)"

az apim create \
  --resource-group $RESOURCE_GROUP \
  --name $APIM_NAME \
  --location $LOCATION \
  --publisher-email $PUBLISHER_EMAIL \
  --publisher-name "$PUBLISHER_NAME" \
  --sku-name $SKU \
  --output table

if [ $? -ne 0 ]; then
    echo "❌ Failed to create API Management instance"
    exit 1
fi

echo "✅ API Management instance created successfully!"
echo "⏰ Completed at: $(date)"

# Get the gateway URL
GATEWAY_URL=$(az apim show \
  --resource-group $RESOURCE_GROUP \
  --name $APIM_NAME \
  --query "gatewayUrl" \
  --output tsv)

echo ""
echo "🎉 Deployment Complete!"
echo "📍 Gateway URL: $GATEWAY_URL"
echo "🔗 Management Portal: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ApiManagement/service/$APIM_NAME"
echo ""
echo "📝 Save these values for next steps:"
echo "  RESOURCE_GROUP=$RESOURCE_GROUP"
echo "  APIM_NAME=$APIM_NAME"
echo "  GATEWAY_URL=$GATEWAY_URL"
echo ""
echo "🔄 Next: Configure OAuth 2.0 and create APIs"