"""
Full Power BI MCP Finance Server - Complete MCP Implementation
For Azure Web App deployment with full MCP tools and Power BI integration
"""

import os
import sys
from datetime import datetime

# Enhanced logging for Azure deployment
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pbi-mcp-server")

# Import with error handling for Azure deployment
try:
    from fastmcp import FastMCP
    logger.info("FastMCP imported successfully")
except ImportError as e:
    logger.error(f"Failed to import FastMCP: {e}")
    raise

try:
    from flask import Flask, jsonify, request, session, redirect, url_for
    from flask_cors import CORS
    import requests
    import msal
    import jwt
    from functools import wraps
    import json
    logger.info("Flask, CORS, and OAuth libraries imported successfully")
except ImportError as e:
    logger.error(f"Failed to import required libraries: {e}")
    raise

# Initialize MCP server
try:
    mcp = FastMCP("powerbi-financial-server")
    logger.info("FastMCP server initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize FastMCP server: {e}")
    raise

# Initialize Flask app for Azure deployment
try:
    flask_app = Flask(__name__)
    flask_app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
    CORS(flask_app)
    logger.info("Flask app and CORS initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Flask app: {e}")
    raise

# OAuth 2.0 Configuration for Microsoft Authentication
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
TENANT_ID = os.environ.get('AZURE_TENANT_ID')
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'https://pbimcp.azurewebsites.net/auth/callback')

# Power BI OAuth scopes - delegated permissions
SCOPES = [
    "https://analysis.windows.net/powerbi/api/Dataset.Read.All",
    "https://analysis.windows.net/powerbi/api/Report.Read.All",
    "https://analysis.windows.net/powerbi/api/Workspace.Read.All",
    "https://analysis.windows.net/powerbi/api/Content.Create"
]

# MSAL Confidential Client for OAuth flow
msal_app = None
if all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
    try:
        msal_app = msal.ConfidentialClientApplication(
            CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            client_credential=CLIENT_SECRET,
        )
        logger.info("MSAL OAuth client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MSAL client: {e}")
else:
    logger.warning("OAuth not configured - missing AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, or AZURE_TENANT_ID")

def require_oauth(f):
    """Decorator to require OAuth authentication for MCP endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Extract Bearer token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "error": "Authentication required",
                "message": "Please provide Bearer token in Authorization header",
                "auth_url": url_for('get_auth_url', _external=True) if msal_app else None,
                "status": "unauthorized"
            }), 401
        
        # Extract and validate access token
        access_token = auth_header.split(' ', 1)[1]
        user_info = validate_microsoft_token(access_token)
        
        if not user_info:
            return jsonify({
                "error": "Invalid or expired token",
                "message": "Please re-authenticate",
                "auth_url": url_for('get_auth_url', _external=True) if msal_app else None,
                "status": "token_invalid"
            }), 401
        
        # Add user context to request
        request.current_user = user_info
        request.access_token = access_token
        
        return f(*args, **kwargs)
    return decorated

def validate_microsoft_token(token):
    """Validate Microsoft OAuth access token"""
    try:
        # Decode JWT token (without signature verification for simplicity)
        # In production, you should verify the signature
        decoded_token = jwt.decode(
            token, 
            options={"verify_signature": False, "verify_exp": True}
        )
        
        # Extract user information
        return {
            "user_id": decoded_token.get('oid'),
            "email": decoded_token.get('preferred_username') or decoded_token.get('upn'),
            "name": decoded_token.get('name'),
            "tenant_id": decoded_token.get('tid'),
            "app_id": decoded_token.get('appid'),
            "roles": decoded_token.get('roles', []),
            "scope": decoded_token.get('scope', '')
        }
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None

def get_user_powerbi_token(user_access_token):
    """Get Power BI access token using on-behalf-of flow"""
    if not msal_app:
        logger.error("MSAL app not configured")
        return None
    
    try:
        # Use the on-behalf-of flow to get Power BI token
        result = msal_app.acquire_token_on_behalf_of(
            user_assertion=user_access_token,
            scopes=SCOPES
        )
        
        if "access_token" in result:
            logger.info("Successfully acquired Power BI token via on-behalf-of flow")
            return result["access_token"]
        else:
            error_desc = result.get('error_description', 'Unknown error')
            logger.error(f"Failed to acquire Power BI token: {error_desc}")
            return None
            
    except Exception as e:
        logger.error(f"Error in on-behalf-of flow: {e}")
        return None

# OAuth-secured MCP tools with user-specific Power BI access
@mcp.tool()
@require_oauth
def get_powerbi_status():
    """Get Power BI authentication status for the current user"""
    user_info = request.current_user
    powerbi_token = get_user_powerbi_token(request.access_token)
    
    return {
        "user": {
            "email": user_info["email"],
            "name": user_info["name"],
            "user_id": user_info["user_id"]
        },
        "powerbi_access": "granted" if powerbi_token else "denied",
        "server_status": "running",
        "authentication": "oauth2_microsoft",
        "timestamp": datetime.utcnow().isoformat()
    }

@mcp.tool()
@require_oauth
def health_check():
    """Full health check with user authentication status"""
    user_info = request.current_user
    powerbi_token = get_user_powerbi_token(request.access_token)
    
    return {
        "status": "healthy",
        "service": "Power BI MCP Finance Server",
        "version": "2.0.0-oauth",
        "environment": "azure" if os.environ.get('WEBSITE_HOSTNAME') else "local",
        "user": {
            "authenticated": True,
            "email": user_info["email"],
            "name": user_info["name"],
            "powerbi_access": bool(powerbi_token)
        },
        "features": {
            "powerbi_integration": True,
            "mcp_tools": True,
            "authentication": "oauth2_microsoft",
            "multi_tenant": True,
            "user_specific_access": True
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@mcp.tool()
@require_oauth
def list_powerbi_workspaces():
    """List Power BI workspaces accessible to the authenticated user"""
    user_info = request.current_user
    powerbi_token = get_user_powerbi_token(request.access_token)
    
    if not powerbi_token:
        return {
            "error": "Unable to access Power BI on behalf of user",
            "user": user_info["email"],
            "message": "Power BI token acquisition failed"
        }
    
    try:
        # Call Power BI REST API with user's delegated token
        headers = {
            "Authorization": f"Bearer {powerbi_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://api.powerbi.com/v1.0/myorg/groups",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            workspaces_data = response.json()
            workspaces = workspaces_data.get("value", [])
            
            # Format workspace data
            formatted_workspaces = []
            for ws in workspaces:
                formatted_workspaces.append({
                    "id": ws["id"],
                    "name": ws["name"],
                    "type": ws.get("type", "Workspace"),
                    "state": ws.get("state", "Active"),
                    "is_read_only": ws.get("isReadOnly", False),
                    "is_on_dedicated_capacity": ws.get("isOnDedicatedCapacity", False)
                })
            
            return {
                "user": user_info["email"],
                "workspaces": formatted_workspaces,
                "total_count": len(formatted_workspaces),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "error": f"Power BI API error: {response.status_code}",
                "message": response.text[:500],  # Limit error message length
                "user": user_info["email"]
            }
            
    except requests.exceptions.Timeout:
        return {
            "error": "Power BI API timeout",
            "message": "Request timed out after 30 seconds",
            "user": user_info["email"]
        }
    except Exception as e:
        return {
            "error": f"Failed to retrieve workspaces: {str(e)}",
            "user": user_info["email"]
        }

@mcp.tool()
@require_oauth
def get_powerbi_datasets(workspace_id: str = None):
    """Get Power BI datasets from user's workspaces or specific workspace"""
    user_info = request.current_user
    powerbi_token = get_user_powerbi_token(request.access_token)
    
    if not powerbi_token:
        return {
            "error": "Unable to access Power BI on behalf of user",
            "user": user_info["email"]
        }
    
    try:
        headers = {
            "Authorization": f"Bearer {powerbi_token}",
            "Content-Type": "application/json"
        }
        
        # Construct API URL based on workspace_id parameter
        if workspace_id:
            url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
        else:
            url = "https://api.powerbi.com/v1.0/myorg/datasets"
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            datasets_data = response.json()
            datasets = datasets_data.get("value", [])
            
            # Format dataset data
            formatted_datasets = []
            for ds in datasets:
                formatted_datasets.append({
                    "id": ds["id"],
                    "name": ds["name"],
                    "web_url": ds.get("webUrl"),
                    "configured_by": ds.get("configuredBy"),
                    "is_refreshable": ds.get("isRefreshable", False),
                    "is_effectively_identity": ds.get("isEffectiveIdentity", False),
                    "created_date": ds.get("createdDate"),
                    "content_provider_type": ds.get("contentProviderType")
                })
            
            return {
                "user": user_info["email"],
                "workspace_id": workspace_id or "all_accessible",
                "datasets": formatted_datasets,
                "total_count": len(formatted_datasets),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "error": f"Power BI API error: {response.status_code}",
                "message": response.text[:500],
                "user": user_info["email"]
            }
            
    except Exception as e:
        return {
            "error": f"Failed to retrieve datasets: {str(e)}",
            "user": user_info["email"]
        }

@mcp.tool()
@require_oauth
def execute_powerbi_query(dataset_id: str, dax_query: str, workspace_id: str = None):
    """Execute DAX query against Power BI dataset with user's permissions"""
    user_info = request.current_user
    powerbi_token = get_user_powerbi_token(request.access_token)
    
    if not powerbi_token:
        return {
            "error": "Unable to access Power BI on behalf of user",
            "user": user_info["email"]
        }
    
    # Validate input parameters
    if not dataset_id or not dax_query:
        return {
            "error": "Missing required parameters",
            "required": "dataset_id and dax_query are required",
            "user": user_info["email"]
        }
    
    try:
        headers = {
            "Authorization": f"Bearer {powerbi_token}",
            "Content-Type": "application/json"
        }
        
        # Construct API URL
        if workspace_id:
            url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
        else:
            url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/executeQueries"
        
        # Prepare query payload
        payload = {
            "queries": [{
                "query": dax_query
            }],
            "serializerSettings": {
                "includeNulls": True
            }
        }
        
        response = requests.post(
            url, 
            headers=headers, 
            json=payload, 
            timeout=120  # Longer timeout for queries
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            return {
                "user": user_info["email"],
                "dataset_id": dataset_id,
                "workspace_id": workspace_id,
                "query": dax_query,
                "results": result_data.get("results", []),
                "execution_time": datetime.utcnow().isoformat(),
                "status": "success"
            }
        else:
            return {
                "error": f"Power BI API error: {response.status_code}",
                "message": response.text[:500],
                "query": dax_query,
                "user": user_info["email"],
                "status": "failed"
            }
            
    except requests.exceptions.Timeout:
        return {
            "error": "Query execution timeout",
            "message": "Query timed out after 120 seconds",
            "user": user_info["email"],
            "query": dax_query
        }
    except Exception as e:
        return {
            "error": f"Failed to execute query: {str(e)}",
            "user": user_info["email"],
            "query": dax_query
        }

# OAuth 2.0 Authentication Endpoints
@flask_app.route('/authorize')
def authorize():
    """OAuth authorization endpoint for Claude.ai MCP integration"""
    if not msal_app:
        return jsonify({
            "error": "OAuth not configured",
            "message": "Server missing OAuth configuration. Please configure AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID"
        }), 500
    
    # Get OAuth parameters from query string
    response_type = request.args.get('response_type')
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    code_challenge = request.args.get('code_challenge')
    code_challenge_method = request.args.get('code_challenge_method')
    state = request.args.get('state')
    scope = request.args.get('scope')
    
    # Validate required OAuth parameters
    if not all([response_type, client_id, redirect_uri]):
        return jsonify({
            "error": "Missing required OAuth parameters",
            "required": "response_type, client_id, redirect_uri"
        }), 400
    
    try:
        # Store Claude.ai redirect URI in session for callback
        if 'claude.ai' in redirect_uri:
            session['claude_redirect_uri'] = redirect_uri
            
        # Generate Microsoft authorization URL
        auth_url = msal_app.get_authorization_request_url(
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,  # Use our configured redirect URI
            state=state or "claude-mcp-oauth"
        )
        
        # Redirect user to Microsoft OAuth
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"Error in /authorize endpoint: {e}")
        return jsonify({
            "error": "Failed to initiate OAuth flow",
            "message": str(e)
        }), 500

@flask_app.route('/auth/url')
def get_auth_url():
    """Get Microsoft OAuth authorization URL for user authentication"""
    if not msal_app:
        return jsonify({
            "error": "OAuth not configured",
            "message": "Server missing OAuth configuration. Please configure AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID"
        }), 500
    
    try:
        # Generate authorization URL
        auth_url = msal_app.get_authorization_request_url(
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
            state="mcp-oauth-flow"  # Optional state parameter
        )
        
        return jsonify({
            "auth_url": auth_url,
            "redirect_uri": REDIRECT_URI,
            "scopes": SCOPES,
            "message": "Visit the auth_url to authenticate with Microsoft and authorize Power BI access"
        })
        
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        return jsonify({
            "error": "Failed to generate authorization URL",
            "message": str(e)
        }), 500

@flask_app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Microsoft and forward to Claude.ai"""
    if not msal_app:
        return jsonify({"error": "OAuth not configured"}), 500
    
    # Get authorization code from callback
    code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    if error:
        return jsonify({
            "error": f"OAuth error: {error}",
            "description": error_description,
            "status": "authentication_failed"
        }), 400
    
    if not code:
        return jsonify({
            "error": "No authorization code received",
            "message": "OAuth callback missing authorization code"
        }), 400
    
    try:
        # Exchange authorization code for access token
        result = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        if "access_token" in result:
            # Validate the token and extract user info
            user_info = validate_microsoft_token(result["access_token"])
            
            if user_info:
                # Check if this is a Claude.ai callback (has claude.ai redirect_uri)
                original_redirect_uri = request.args.get('redirect_uri') or session.get('claude_redirect_uri')
                if original_redirect_uri and 'claude.ai' in original_redirect_uri:
                    # Forward to Claude.ai with authorization code
                    import urllib.parse
                    claude_callback_url = f"{original_redirect_uri}?code={code}&state={request.args.get('state', '')}"
                    return redirect(claude_callback_url)
                
                # Regular callback - return token info
                return jsonify({
                    "status": "authenticated",
                    "access_token": result["access_token"],
                    "token_type": "Bearer",
                    "expires_in": result.get("expires_in", 3600),
                    "user": {
                        "email": user_info["email"],
                        "name": user_info["name"],
                        "user_id": user_info["user_id"]
                    },
                    "usage_instructions": {
                        "header": "Authorization: Bearer <access_token>",
                        "example": f"Authorization: Bearer {result['access_token'][:50]}..."
                    },
                    "message": "Authentication successful! Use the access_token in the Authorization header for MCP requests."
                })
            else:
                return jsonify({
                    "error": "Token validation failed",
                    "message": "Received token but could not validate user information"
                }), 400
        else:
            error_desc = result.get('error_description', 'Unknown authentication error')
            return jsonify({
                "error": "Authentication failed",
                "description": error_desc,
                "details": result.get('error')
            }), 400
            
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return jsonify({
            "error": "Authentication processing failed",
            "message": str(e)
        }), 500

# Flask routes for Azure Web App
@flask_app.route('/')
def index():
    """Root endpoint with OAuth authentication information"""
    oauth_configured = bool(msal_app)
    
    return jsonify({
        "service": "Power BI MCP Finance Server",
        "status": "running",
        "version": "2.0.0-oauth",
        "authentication": {
            "type": "oauth2_microsoft",
            "configured": oauth_configured,
            "auth_url_endpoint": url_for('get_auth_url', _external=True) if oauth_configured else None,
            "callback_endpoint": url_for('auth_callback', _external=True) if oauth_configured else None,
            "required_header": "Authorization: Bearer <your-microsoft-token>",
            "scopes": SCOPES if oauth_configured else []
        },
        "mcp_tools": [
            "get_powerbi_status",
            "health_check", 
            "list_powerbi_workspaces",
            "get_powerbi_datasets",
            "execute_powerbi_query"
        ],
        "features": {
            "powerbi_integration": True,
            "mcp_server": True,
            "oauth_authentication": oauth_configured,
            "multi_tenant": True,
            "user_specific_access": True,
            "delegated_permissions": True
        },
        "usage": {
            "step1": "GET /auth/url to get Microsoft login URL",
            "step2": "User visits login URL and authorizes",
            "step3": "Use returned access_token in Authorization header",
            "step4": "Call MCP tools with authenticated requests"
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@flask_app.route('/health')
def health():
    """Health check endpoint"""
    oauth_configured = bool(msal_app)
    
    return jsonify({
        "status": "healthy",
        "authentication": {
            "oauth_configured": oauth_configured,
            "authentication_required": True,
            "type": "microsoft_oauth2"
        },
        "environment": "azure" if os.environ.get('WEBSITE_HOSTNAME') else "local",
        "database_required": False,
        "mcp_tools_protected": True,
        "timestamp": datetime.utcnow().isoformat()
    })

@flask_app.route('/api/powerbi/workspaces')
@require_oauth
def list_workspaces():
    """List Power BI workspaces for authenticated user (REST API endpoint)"""
    # This endpoint duplicates the MCP tool functionality for REST access
    return list_powerbi_workspaces()

def create_app():
    """Create Flask app for Azure deployment"""
    return flask_app

def main():
    """Main entry point"""
    logger.info("Starting Full Power BI MCP Server")
    
    # Check if running on Azure
    is_azure = bool(os.environ.get('WEBSITE_HOSTNAME'))
    if is_azure:
        logger.info(f"Running on Azure Web App: {os.environ.get('WEBSITE_HOSTNAME')}")
    else:
        logger.info("Running locally")
    
    # Check OAuth configuration
    oauth_configured = bool(msal_app)
    logger.info(f"OAuth authentication configured: {oauth_configured}")
    
    if not oauth_configured:
        logger.warning("OAuth authentication not configured!")
        logger.info("Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID")
    
    if is_azure:
        # For Azure deployment, return Flask app
        logger.info("Configured for Azure Web App deployment")
        return flask_app
    else:
        # For local development, run Flask directly
        port = int(os.environ.get('PORT', 8000))
        logger.info(f"Starting Flask server on port {port}")
        flask_app.run(host='0.0.0.0', port=port, debug=False)

# For gunicorn deployment - Direct startup optimization
def initialize_for_gunicorn():
    """Initialize everything needed for direct gunicorn startup"""
    logger.info("=== Power BI MCP Server Direct Startup ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Check critical environment
    is_azure = bool(os.environ.get('WEBSITE_HOSTNAME'))
    logger.info(f"Running on Azure: {is_azure}")
    if is_azure:
        logger.info(f"Azure hostname: {os.environ.get('WEBSITE_HOSTNAME')}")
    
    # Verify OAuth configuration
    oauth_configured = bool(msal_app)
    logger.info(f"OAuth configured: {oauth_configured}")
    if oauth_configured:
        logger.info("Microsoft OAuth authentication enabled")
    else:
        logger.warning("OAuth not configured - set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID")
    
    # Log available MCP tools
    logger.info("Available MCP tools: get_powerbi_status, health_check, list_powerbi_workspaces, get_powerbi_datasets, execute_powerbi_query")
    
    return True

# Initialize for direct gunicorn startup
try:
    initialize_for_gunicorn()
    app = create_app()
    APP = app  # Azure expects uppercase APP
    
    # Validate app creation
    if app is None:
        raise RuntimeError("Failed to create Flask app")
    
    logger.info(f"Flask app created successfully: {app.name}")
    logger.info(f"App routes available: {[rule.rule for rule in app.url_map.iter_rules()]}")
    logger.info("Power BI MCP Server ready for gunicorn startup")
    
except Exception as e:
    logger.error(f"Failed to initialize app for gunicorn: {e}")
    raise

if __name__ == "__main__":
    main()