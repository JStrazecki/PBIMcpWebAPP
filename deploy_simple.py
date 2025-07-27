#!/usr/bin/env python3
"""
Simplified Azure deployment version of PBI MCP Finance Server
Uses Flask only for Azure Web App compatibility
"""

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

# Import your existing modules
try:
    from pbi_mcp_finance.auth.oauth_manager import get_token_manager, get_powerbi_token
    from pbi_mcp_finance.utils.logging import get_logger
    from pbi_mcp_finance.config.settings import settings
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import PBI modules: {e}")
    MODULES_AVAILABLE = False

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
CORS(app)

logger = get_logger("deploy_simple") if MODULES_AVAILABLE else None

@app.route('/')
def health_check():
    """Health check endpoint for Azure"""
    return jsonify({
        "status": "healthy",
        "service": "Power BI MCP Finance Server (Simplified)",
        "version": "1.0.0-azure",
        "timestamp": datetime.utcnow().isoformat(),
        "modules_loaded": MODULES_AVAILABLE
    })

@app.route('/health')
def health():
    """Detailed health check"""
    if not MODULES_AVAILABLE:
        return jsonify({
            "status": "degraded",
            "error": "PBI modules not available",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    try:
        token_manager = get_token_manager()
        token_info = token_manager.get_token_info()
        
        return jsonify({
            "status": "healthy",
            "powerbi_auth": token_info.get('status', 'unknown'),
            "environment": "azure-production",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/api/powerbi/workspaces')
def list_workspaces():
    """List Power BI workspaces"""
    if not MODULES_AVAILABLE:
        return jsonify({"error": "Modules not available"}), 503
    
    try:
        # Add your Power BI workspace listing logic here
        return jsonify({
            "workspaces": [],
            "message": "Power BI integration placeholder"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting simplified PBI MCP server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)