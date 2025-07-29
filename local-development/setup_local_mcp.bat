@echo off
echo Setting up local MCP server for Claude.ai testing...

REM Set environment variables (replace with your actual values)
set AZURE_CLIENT_ID=your-client-id-here
set AZURE_CLIENT_SECRET=your-client-secret-here  
set AZURE_TENANT_ID=your-tenant-id-here

echo.
echo Environment variables set:
echo AZURE_CLIENT_ID=%AZURE_CLIENT_ID%
echo AZURE_TENANT_ID=%AZURE_TENANT_ID%
echo AZURE_CLIENT_SECRET=[HIDDEN]

echo.
echo Testing MCP server import...
python -c "from mcp_server import mcp; print('✓ MCP server imports successfully')"

if %ERRORLEVEL% NEQ 0 (
    echo ✗ MCP server import failed
    pause
    exit /b 1
)

echo.
echo ✓ Local MCP server setup complete!
echo.
echo Next steps:
echo 1. Replace the placeholder values above with your actual Azure credentials
echo 2. Update Claude Desktop config at: %APPDATA%\Claude\claude_desktop_config.json
echo 3. Add this configuration:
echo.
echo {
echo   "mcpServers": {
echo     "powerbi-server": {
echo       "command": "python",
echo       "args": ["%CD%\mcp_server.py"],
echo       "env": {
echo         "AZURE_CLIENT_ID": "%AZURE_CLIENT_ID%",
echo         "AZURE_CLIENT_SECRET": "%AZURE_CLIENT_SECRET%",
echo         "AZURE_TENANT_ID": "%AZURE_TENANT_ID%"
echo       }
echo     }
echo   }
echo }
echo.
echo 4. Restart Claude Desktop
echo 5. Test MCP connection

pause