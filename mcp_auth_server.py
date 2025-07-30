"""
Authenticated MCP Server for Claude AI
Requires Microsoft OAuth for user authentication
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from flask import Flask, request, jsonify, redirect, session, url_for
from flask_cors import CORS
import requests
import secrets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("pbi-mcp-auth")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
CORS(app)

# Microsoft OAuth Configuration
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET', '')
TENANT_ID = os.environ.get('AZURE_TENANT_ID', '')

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({"error": "Authentication required", "auth_url": "/auth"}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def home():
    """MCP Server information"""
    return jsonify({
        "name": "Power BI MCP Server (Authenticated)",
        "version": "1.0.0",
        "type": "remote_mcp_server",
        "authentication": "required",
        "auth_url": "/auth",
        "capabilities": ["powerbi_workspaces", "powerbi_datasets", "powerbi_queries"],
        "claude_oauth": {
            "authorization_url": f"{request.base_url.rstrip('/')}/auth",
            "callback_url": "https://claude.ai/api/mcp/auth_callback"
        }
    })

@app.route('/auth')
def auth():
    """Microsoft OAuth authentication"""
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        return jsonify({
            "error": "OAuth not configured",
            "message": "Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID"
        }), 500
    
    # Generate secure state
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Microsoft OAuth URL
    redirect_uri = url_for('callback', _external=True)
    auth_url = (
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&scope=openid profile User.Read"
        f"&state={state}"
        f"&prompt=select_account"
    )
    
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """OAuth callback"""
    # Verify state
    received_state = request.args.get('state')
    expected_state = session.get('oauth_state')
    
    if not received_state or received_state != expected_state:
        return jsonify({"error": "Invalid state parameter"}), 400
    
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return jsonify({
            "error": "Authentication failed", 
            "details": request.args.get('error_description', error)
        }), 400
    
    if not code:
        return jsonify({"error": "No authorization code received"}), 400
    
    try:
        # Exchange code for token
        token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
        token_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': 'openid profile User.Read',
            'code': code,
            'redirect_uri': url_for('callback', _external=True),
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.post(token_url, data=token_data, timeout=30)
        
        if token_response.status_code == 200:
            token_info = token_response.json()
            access_token = token_info.get('access_token')
            
            # Get user info
            user_response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=30
            )
            
            if user_response.status_code == 200:
                user_info = user_response.json()
                
                # Store user session (no token storage)
                session['authenticated'] = True
                session['auth_time'] = datetime.utcnow().isoformat()
                session['user_name'] = user_info.get('displayName', 'Unknown')
                session['user_email'] = user_info.get('userPrincipalName', 'unknown')
                
                session.pop('oauth_state', None)
                
                return jsonify({
                    "message": "Authentication successful",
                    "user": {
                        "name": session['user_name'],
                        "email": session['user_email']
                    },
                    "redirect": "/"
                })
            else:
                return jsonify({"error": "Failed to get user info"}), 400
        else:
            return jsonify({"error": "Token exchange failed"}), 400
            
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return jsonify({"error": f"Authentication failed: {str(e)}"}), 500

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@app.route('/health')
@require_auth
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "Power BI MCP Server (Authenticated)",
        "user": session.get('user_name', 'Unknown'),
        "authenticated": True,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/workspaces')
@require_auth
def workspaces():
    """List Power BI workspaces (demo data)"""
    demo_workspaces = [
        {"id": "ws-1", "name": "Finance Reports", "type": "Workspace"},
        {"id": "ws-2", "name": "Sales Analytics", "type": "Workspace"},
        {"id": "ws-3", "name": "Operations Dashboard", "type": "Workspace"}
    ]
    
    return jsonify({
        "workspaces": demo_workspaces,
        "user": session.get('user_name'),
        "authenticated": True,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/datasets')
@require_auth
def datasets():
    """Get Power BI datasets (demo data)"""
    workspace_id = request.args.get('workspace_id')
    
    demo_datasets = [
        {"id": "ds-1", "name": "Financial KPIs", "workspace_id": "ws-1"},
        {"id": "ds-2", "name": "Sales Performance", "workspace_id": "ws-2"},
        {"id": "ds-3", "name": "Operations Metrics", "workspace_id": "ws-3"}
    ]
    
    if workspace_id:
        demo_datasets = [ds for ds in demo_datasets if ds["workspace_id"] == workspace_id]
    
    return jsonify({
        "datasets": demo_datasets,
        "workspace_id": workspace_id,
        "user": session.get('user_name'),
        "authenticated": True,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/query', methods=['POST'])
@require_auth
def query():
    """Execute Power BI query (demo data)"""
    data = request.get_json()
    dataset_id = data.get('dataset_id') if data else None
    query_text = data.get('query') if data else None
    
    if not dataset_id:
        return jsonify({"error": "dataset_id required"}), 400
    
    # Demo results
    demo_results = [
        {"metric": "Revenue", "value": 1250000, "period": "Q1 2024"},
        {"metric": "Profit", "value": 350000, "period": "Q1 2024"}
    ]
    
    return jsonify({
        "dataset_id": dataset_id,
        "query": query_text,
        "results": demo_results,
        "user": session.get('user_name'),
        "authenticated": True,
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        logger.warning("OAuth not configured - set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID")
    
    logger.info(f"Starting Authenticated MCP Server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)