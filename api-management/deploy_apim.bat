@echo off
REM Azure API Management Deployment Script for Power BI MCP Server (Windows)

echo 🚀 Deploying Azure API Management for Power BI MCP Server...

REM Configuration variables (update these as needed)
set RESOURCE_GROUP=rg-pbi-mcp-enterprise
set LOCATION=eastus
set APIM_NAME=pbi-mcp-apim-%RANDOM%
set PUBLISHER_EMAIL=admin@company.com
set PUBLISHER_NAME=Power BI MCP Enterprise
set SKU=Developer

echo 📋 Configuration:
echo   Resource Group: %RESOURCE_GROUP%
echo   Location: %LOCATION%
echo   APIM Name: %APIM_NAME%
echo   SKU: %SKU%
echo.

REM Create resource group
echo 🏗️  Creating resource group...
call az group create --name %RESOURCE_GROUP% --location %LOCATION% --output table

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to create resource group
    pause
    exit /b 1
)

REM Create API Management instance
echo 🔧 Creating API Management instance (this takes 15-30 minutes)...
echo ⏰ Started at: %DATE% %TIME%

call az apim create ^
  --resource-group %RESOURCE_GROUP% ^
  --name %APIM_NAME% ^
  --location %LOCATION% ^
  --publisher-email %PUBLISHER_EMAIL% ^
  --publisher-name "%PUBLISHER_NAME%" ^
  --sku-name %SKU% ^
  --output table

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to create API Management instance
    pause
    exit /b 1
)

echo ✅ API Management instance created successfully!
echo ⏰ Completed at: %DATE% %TIME%

REM Get the gateway URL
for /f "tokens=*" %%i in ('az apim show --resource-group %RESOURCE_GROUP% --name %APIM_NAME% --query "gatewayUrl" --output tsv') do set GATEWAY_URL=%%i

echo.
echo 🎉 Deployment Complete!
echo 📍 Gateway URL: %GATEWAY_URL%
echo 🔗 Management Portal: https://portal.azure.com
echo.
echo 📝 Save these values for next steps:
echo   RESOURCE_GROUP=%RESOURCE_GROUP%
echo   APIM_NAME=%APIM_NAME%
echo   GATEWAY_URL=%GATEWAY_URL%
echo.
echo 🔄 Next: Configure OAuth 2.0 and create APIs

pause