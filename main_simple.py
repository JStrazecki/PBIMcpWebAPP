"""
Simplified Power BI MCP Finance Server - NO DATABASE DEPENDENCIES
For Azure Web App deployment without SQLite requirements
"""

import os
import sys
from datetime import datetime
from fastmcp import FastMCP
from flask import Flask, jsonify
from flask_cors import CORS

# Simple logging without database
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pbi-mcp-simple")

# Initialize MCP server
mcp = FastMCP("powerbi-financial-server-simple")

# Initialize Flask app for Azure deployment
flask_app = Flask(__name__)
flask_app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
CORS(flask_app)

# Simple Power BI authentication check
def check_powerbi_auth():
    """Simple Power BI authentication check without database"""
    # Check for manual token
    manual_token = os.environ.get('POWERBI_TOKEN')
    if manual_token:
        return {"status": "ready", "type": "manual_token"}
    
    # Check for OAuth credentials
    client_id = os.environ.get('POWERBI_CLIENT_ID')
    client_secret = os.environ.get('POWERBI_CLIENT_SECRET')
    tenant_id = os.environ.get('POWERBI_TENANT_ID')
    
    if all([client_id, client_secret, tenant_id]):
        return {"status": "ready", "type": "oauth"}
    
    return {"status": "not_configured", "type": "none"}

# Simple MCP tools without database dependencies
@mcp.tool()
def get_powerbi_status():
    """Get Power BI authentication status"""
    auth_status = check_powerbi_auth()
    return {
        "powerbi_auth": auth_status["status"],
        "auth_type": auth_status["type"],
        "server_status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@mcp.tool()
def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "service": "Power BI MCP Finance Server (Simplified)",
        "version": "1.0.0-simple",
        "database": "disabled",
        "timestamp": datetime.utcnow().isoformat()
    }

# Flask routes for Azure Web App
@flask_app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        "service": "Power BI MCP Finance Server (Simplified)",
        "status": "running",
        "version": "1.0.0-simple",
        "powerbi_auth": check_powerbi_auth(),
        "features": {
            "database": "disabled",
            "conversation_tracking": "disabled",
            "metrics": "disabled"
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@flask_app.route('/health')
def health():
    """Health check endpoint"""
    auth_status = check_powerbi_auth()
    
    return jsonify({
        "status": "healthy",
        "powerbi_auth": auth_status["status"],
        "environment": "azure-simple" if os.environ.get('WEBSITE_HOSTNAME') else "local",
        "database_required": False,
        "timestamp": datetime.utcnow().isoformat()
    })

@flask_app.route('/api/powerbi/workspaces')
def list_workspaces():
    """Placeholder for Power BI workspaces"""
    auth_status = check_powerbi_auth()
    
    if auth_status["status"] != "ready":
        return jsonify({
            "error": "Power BI not configured",
            "required": "POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET, POWERBI_TENANT_ID or POWERBI_TOKEN"
        }), 503
    
    return jsonify({
        "message": "Power BI integration ready",
        "workspaces": [],
        "note": "Implement actual Power BI API calls here"
    })

def create_app():
    """Create Flask app for Azure deployment"""
    return flask_app

def main():
    """Main entry point"""
    logger.info("Starting Simplified Power BI MCP Server")
    
    # Check if running on Azure
    is_azure = bool(os.environ.get('WEBSITE_HOSTNAME'))
    if is_azure:
        logger.info(f"Running on Azure Web App: {os.environ.get('WEBSITE_HOSTNAME')}")
    else:
        logger.info("Running locally")
    
    # Check authentication
    auth_status = check_powerbi_auth()
    logger.info(f"Power BI authentication: {auth_status}")
    
    if auth_status["status"] == "not_configured":
        logger.warning("Power BI authentication not configured!")
        logger.info("Set POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET, POWERBI_TENANT_ID")
        logger.info("Or set POWERBI_TOKEN for manual authentication")
    
    if is_azure:
        # For Azure deployment, return Flask app
        logger.info("Configured for Azure Web App deployment")
        return flask_app
    else:
        # For local development, run Flask directly
        port = int(os.environ.get('PORT', 8000))
        logger.info(f"Starting Flask server on port {port}")
        flask_app.run(host='0.0.0.0', port=port, debug=False)

# For gunicorn deployment
app = create_app()

# Validate app creation
if app is None:
    raise RuntimeError("Failed to create Flask app")

logger.info(f"✅ Flask app created successfully: {app.name}")
logger.info(f"✅ App routes: {[rule.rule for rule in app.url_map.iter_rules()]}")

if __name__ == "__main__":
    main()