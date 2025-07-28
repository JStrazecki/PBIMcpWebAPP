"""
Simplified Power BI MCP Server - Matching Working Example Pattern
Based on successful SQL Assistant Bot architecture
"""

import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging

# Simple logging (matching working example)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pbi-mcp-server")

# Initialize Flask app (exactly like working example structure)
flask_app = Flask(__name__)
flask_app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
CORS(flask_app)

# Simple Power BI authentication check
def check_powerbi_auth():
    """Simple Power BI authentication check"""
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

# Flask routes (matching working example pattern)
@flask_app.route('/')
def index():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return jsonify({
        "service": "Power BI MCP Finance Server",
        "status": "running",
        "version": "1.0.0",
        "powerbi_auth": check_powerbi_auth(),
        "timestamp": datetime.utcnow().isoformat(),
        "message": "PBI MCP Server is running successfully"
    })

@flask_app.route('/health')
def health():
    """Health check endpoint"""
    logger.info("Health check accessed")
    auth_status = check_powerbi_auth()
    
    return jsonify({
        "status": "healthy",
        "powerbi_auth": auth_status["status"],
        "environment": "azure" if os.environ.get('WEBSITE_HOSTNAME') else "local",
        "timestamp": datetime.utcnow().isoformat()
    })

@flask_app.route('/api/powerbi/status')
def powerbi_status():
    """Power BI status endpoint"""
    logger.info("PowerBI status check")
    auth_status = check_powerbi_auth()
    
    if auth_status["status"] != "ready":
        return jsonify({
            "error": "Power BI not configured",
            "required": "POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET, POWERBI_TENANT_ID or POWERBI_TOKEN",
            "current_status": auth_status
        }), 503
    
    return jsonify({
        "message": "Power BI integration ready",
        "auth_type": auth_status["type"],
        "status": "configured"
    })

@flask_app.route('/api/powerbi/workspaces')
def list_workspaces():
    """Placeholder for Power BI workspaces"""
    logger.info("Workspaces endpoint accessed")
    auth_status = check_powerbi_auth()
    
    if auth_status["status"] != "ready":
        return jsonify({
            "error": "Power BI not configured",
            "required": "POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET, POWERBI_TENANT_ID or POWERBI_TOKEN"
        }), 503
    
    return jsonify({
        "message": "Power BI integration ready",
        "workspaces": [],
        "note": "Implement actual Power BI API calls here",
        "auth_type": auth_status["type"]
    })

def create_app():
    """Create Flask app for Azure deployment (matching working example)"""
    logger.info("Creating Flask app for deployment")
    return flask_app

def main():
    """Main entry point (matching working example pattern)"""
    logger.info("Starting Power BI MCP Server")
    
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

# For gunicorn deployment (exactly matching working example)
app = create_app()
APP = app  # Azure expects uppercase APP

# Validate app creation (matching working example)
if app is None:
    raise RuntimeError("Failed to create Flask app")

logger.info(f"Flask app created successfully: {app.name}")
logger.info(f"App routes: {[rule.rule for rule in app.url_map.iter_rules()]}")

# Test message to confirm app loads
logger.info("✓ Power BI MCP Server app loads successfully")

if __name__ == "__main__":
    main()