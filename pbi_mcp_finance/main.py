"""
Main entry point for Power BI MCP Finance Server
Modularized version with clean architecture
"""

import os
import sys
from datetime import datetime
from fastmcp import FastMCP
from flask import Flask
from flask_cors import CORS

from .config.settings import settings
from .auth.oauth_manager import get_token_manager, get_powerbi_token
from .auth.microsoft_oauth import get_oauth_instance
from .utils.logging import get_logger, mcp_logger
from .mcp.tools.workspace_tools import register_workspace_tools
from .mcp.tools.financial_tools import register_financial_tools
from .mcp.tools.query_tools import register_query_tools
from .mcp.tools.admin_tools import register_admin_tools
from .mcp.tools.monitoring_tools import register_monitoring_tools
from .mcp.tools.model_discovery_tools import register_model_discovery_tools
from .mcp.tools.financial_statement_tools import register_financial_statement_tools
from .context.resources import register_context_resources

# Initialize server
mcp = FastMCP("powerbi-financial-server")
logger = get_logger("main")

# Initialize Flask app for OAuth endpoints (if authentication is enabled)
flask_app = None
if os.environ.get('AUTH_ENABLED', '').lower() in ('true', '1', 'yes'):
    flask_app = Flask(__name__)
    flask_app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
    CORS(flask_app)
    
    # Initialize OAuth with Flask app
    oauth_instance = get_oauth_instance()
    oauth_instance.init_app(flask_app)


def setup_authentication():
    """Setup and validate authentication"""
    auth_enabled = os.environ.get('AUTH_ENABLED', '').lower() in ('true', '1', 'yes')
    
    if auth_enabled:
        logger.info("🔐 Web authentication enabled")
        oauth_instance = get_oauth_instance()
        if oauth_instance._is_configured():
            logger.info("✅ Microsoft OAuth configured")
            logger.info("🌐 Authentication endpoints available at:")
            logger.info("  - /auth/login - Start authentication")
            logger.info("  - /auth/logout - Sign out")
            logger.info("  - /auth/status - Check auth status")
        else:
            logger.warning("⚠️ Authentication enabled but OAuth not configured")
            logger.info("Set these environment variables:")
            logger.info("  - AZURE_CLIENT_ID")
            logger.info("  - AZURE_CLIENT_SECRET") 
            logger.info("  - AZURE_TENANT_ID")
            logger.info("  - AZURE_REDIRECT_URI (optional)")
    else:
        logger.info("🔓 Web authentication disabled (AUTH_ENABLED not set)")
    
    # Check Power BI token availability
    token_manager = get_token_manager()
    auth_token = get_powerbi_token()
    
    if not auth_token:
        logger.critical("❌ No Power BI token available!")
        logger.info("\nAuthentication Options:")
        logger.info("Option 1 - Manual Token (Quick Start): Set POWERBI_TOKEN environment variable")
        logger.info("Option 2 - OAuth2 (Auto-refresh): Set these environment variables:")
        logger.info("  - POWERBI_CLIENT_ID")
        logger.info("  - POWERBI_CLIENT_SECRET")
        logger.info("  - POWERBI_TENANT_ID")
        logger.info("\nSee AZURE_AD_OAUTH2_SETUP.md for OAuth2 setup instructions")
        sys.exit(1)
    else:
        logger.info("✅ Power BI authentication ready")
        token_info = token_manager.get_token_info()
        
        if token_info.get('using_manual_token', False):
            logger.info("🔑 Using manual bearer token")
            if token_info.get('oauth_configured', False):
                logger.info("ℹ️ OAuth2 is configured as fallback when manual token expires")
            else:
                logger.info("ℹ️ OAuth2 not configured - only manual token available")
        else:
            logger.info("🔧 Using OAuth2 automatic token management")
            logger.info("ℹ️ Manual token can be set as POWERBI_TOKEN for override")


def register_all_tools():
    """Register all MCP tools"""
    logger.info("Registering MCP tools...")
    
    # Register all tool modules
    register_workspace_tools(mcp)
    register_financial_tools(mcp)
    register_query_tools(mcp)
    register_admin_tools(mcp)
    register_monitoring_tools(mcp)
    register_model_discovery_tools(mcp)
    register_financial_statement_tools(mcp)
    
    logger.info("All tools registered successfully")


def register_context_system():
    """Register context resources for automatic injection"""
    logger.info("Registering Power BI context resources...")
    
    # Register context resources - these auto-inject into Claude conversations
    register_context_resources(mcp)
    
    logger.info("Context system registered - Claude will receive Power BI model info automatically!")


def create_flask_app():
    """Create and configure Flask app for Azure deployment"""
    if not flask_app:
        return None
    
    @flask_app.route('/')
    def health_check():
        """Health check endpoint for Azure"""
        return {
            "status": "healthy",
            "service": "Power BI MCP Finance Server",
            "version": "1.0.0",
            "authentication": os.environ.get('AUTH_ENABLED', 'false').lower() in ('true', '1', 'yes'),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @flask_app.route('/health')
    def health():
        """Detailed health check"""
        token_manager = get_token_manager()
        token_info = token_manager.get_token_info()
        
        return {
            "status": "healthy",
            "powerbi_auth": token_info.get('status', 'unknown'),
            "oauth_configured": get_oauth_instance()._is_configured() if flask_app else False,
            "environment": "production" if os.environ.get('WEBSITE_HOSTNAME') else "development"
        }
    
    return flask_app


def main():
    """Main entry point"""
    logger.info("Starting Enhanced Power BI MCP Server")
    
    # Check if running on Azure
    is_azure = bool(os.environ.get('WEBSITE_HOSTNAME'))
    if is_azure:
        logger.info(f"🌐 Running on Azure Web App: {os.environ.get('WEBSITE_HOSTNAME')}")
    else:
        logger.info("💻 Running locally")
    
    logger.info("Conversation tracking enabled")
    logger.info(f"Shared databases: {settings.shared_dir}")
    
    try:
        # Setup authentication
        setup_authentication()
        
        # Register tools
        register_all_tools()
        
        # Register context resources for automatic injection  
        register_context_system()
        
        # For Azure deployment, return Flask app for gunicorn
        if is_azure and flask_app:
            logger.info("🚀 Configured for Azure Web App deployment")
            return create_flask_app()
        
        # For local development, run both servers
        auth_enabled = os.environ.get('AUTH_ENABLED', '').lower() in ('true', '1', 'yes')
        if auth_enabled and flask_app:
            import threading
            def run_flask():
                port = int(os.environ.get('AUTH_PORT', 8000))
                logger.info(f"🌐 Starting authentication server on port {port}")
                flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
            
            flask_thread = threading.Thread(target=run_flask, daemon=True)
            flask_thread.start()
            logger.info("✅ Authentication server started")
        
        # Start MCP server (local only)
        logger.info("Server starting...")
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.critical(f"Server startup failed: {e}")
        sys.exit(1)
    finally:
        logger.info("Server shutdown complete")


# Create Flask app instance for gunicorn
app = None

def get_app():
    """Get or create the Flask app for gunicorn"""
    global app
    if app is None:
        # Initialize the application
        setup_authentication()
        register_all_tools()
        register_context_system()
        app = create_flask_app()
    return app

# For gunicorn deployment
app = get_app()

if __name__ == "__main__":
    main()