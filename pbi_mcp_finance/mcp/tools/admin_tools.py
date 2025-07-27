"""
MCP tools for administrative functions and system management
"""

from fastmcp import FastMCP

from ...auth.oauth_manager import get_token_manager, get_powerbi_token
from ...config.settings import settings
from ...utils.logging import mcp_logger
from ...utils.exceptions import AuthenticationError


def register_admin_tools(mcp: FastMCP):
    """Register administrative MCP tools"""
    
    @mcp.tool()
    def check_token_status() -> str:
        """
        Check the status of the current Power BI token (manual or OAuth2).
        
        Returns:
            Detailed information about the current token status
        """
        try:
            mcp_logger.info("Checking token status")
            
            token_manager = get_token_manager()
            token_info = token_manager.get_token_info()
            
            output = "🔐 Power BI Token Status\n"
            output += "="*40 + "\n\n"
            
            # Token type and status
            token_type = token_info.get('type', 'Unknown')
            status = token_info.get('status', 'Unknown')
            using_manual = token_info.get('using_manual_token', False)
            
            output += f"📋 Token Type: {token_type}\n"
            
            if status == 'Valid':
                output += "✅ Token Status: Valid\n"
            elif status == 'Expired':
                output += "❌ Token Status: Expired\n"
            else:
                output += f"⚠️ Token Status: {status}\n"
            
            # Expiration info
            expires_at = token_info.get('expires_at')
            if expires_at:
                output += f"📅 Expires At: {expires_at}\n"
            
            # Configuration status
            output += "\n🔧 Configuration:\n"
            if using_manual:
                output += "• Using Manual Bearer Token (Priority 1)\n"
                manual_token = settings.powerbi_manual_token
                output += f"• Manual Token: {'Configured' if manual_token else 'Missing'}\n"
            
            oauth_configured = token_info.get('oauth_configured', False)
            if oauth_configured:
                output += "• OAuth2: Configured (Fallback)\n"
                output += f"• Client ID: {'Set' if token_manager.client_id else 'Missing'}\n"
                output += f"• Client Secret: {'Set' if token_manager.client_secret else 'Missing'}\n"
                output += f"• Tenant ID: {'Set' if token_manager.tenant_id else 'Missing'}\n"
                
                if not using_manual:
                    has_refresh = token_info.get('has_refresh_token', False)
                    output += f"• Refresh Token: {'Available' if has_refresh else 'Not available'}\n"
            else:
                output += "• OAuth2: Not configured\n"
            
            # Test token validity with a simple API call
            test_headers = {"Authorization": f"Bearer {get_powerbi_token()}"} if get_powerbi_token() else {}
            if test_headers:
                try:
                    import requests
                    test_response = requests.get(
                        f"{settings.fabric_api_base_url}/workspaces", 
                        headers=test_headers,
                        timeout=10
                    )
                    if test_response.status_code == 200:
                        output += "\n✅ API Test: Token works correctly\n"
                    elif test_response.status_code == 401:
                        output += "\n❌ API Test: Authentication failed\n"
                    else:
                        output += f"\n⚠️ API Test: Unexpected response ({test_response.status_code})\n"
                except Exception as e:
                    output += f"\n❌ API Test: Network error - {str(e)}\n"
            else:
                output += "\n❌ API Test: No token available\n"
            
            return output
            
        except Exception as e:
            mcp_logger.error(f"Failed to check token status: {e}")
            return f"❌ Error checking token status: {str(e)}"
    
    @mcp.tool()
    def refresh_powerbi_token() -> str:
        """
        Manually refresh the Power BI OAuth2 token (only applicable when using OAuth2).
        
        Returns:
            Result of the token refresh operation
        """
        try:
            mcp_logger.info("Attempting to refresh token")
            
            token_manager = get_token_manager()
            token_info = token_manager.get_token_info()
            
            # Check if using manual token
            if token_info.get('using_manual_token', False):
                return "ℹ️ Currently using manual bearer token.\n" + \
                       "Manual tokens cannot be refreshed automatically.\n" + \
                       "To update your token, set a new value for POWERBI_TOKEN environment variable."
            
            # Check if OAuth2 is configured
            if not token_manager._has_oauth_config():
                return "❌ OAuth2 not configured. Cannot refresh token automatically.\n" + \
                       "Please configure POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET, and POWERBI_TENANT_ID environment variables."
            
            output = "🔄 Refreshing OAuth2 Token...\n"
            output += "="*35 + "\n\n"
            
            # Get current token info
            old_info = token_manager.get_token_info()
            output += f"Old Status: {old_info.get('status', 'Unknown')}\n"
            
            # Invalidate current token to force refresh
            token_manager.invalidate_token()
            output += "🗑️ Invalidated current token\n"
            
            # Get new token
            new_token = token_manager.get_valid_token()
            
            if new_token:
                new_info = token_manager.get_token_info()
                output += "✅ Token refresh successful!\n"
                output += f"New Status: {new_info.get('status', 'Unknown')}\n"
                
                expires_at = new_info.get('expires_at')
                if expires_at:
                    output += f"📅 New Expiry: {expires_at}\n"
                
                # Test the new token
                test_headers = {"Authorization": f"Bearer {new_token}"}
                try:
                    import requests
                    test_response = requests.get(
                        f"{settings.fabric_api_base_url}/workspaces", 
                        headers=test_headers,
                        timeout=10
                    )
                    if test_response.status_code == 200:
                        output += "✅ Token validation: Success\n"
                    else:
                        output += f"⚠️ Token validation: Unexpected response ({test_response.status_code})\n"
                except Exception as e:
                    output += f"❌ Token validation: {str(e)}\n"
                    
            else:
                output += "❌ Token refresh failed!\n"
                output += "Check your OAuth2 configuration and network connection.\n"
            
            return output
            
        except Exception as e:
            mcp_logger.error(f"Failed to refresh token: {e}")
            return f"❌ Error refreshing token: {str(e)}"