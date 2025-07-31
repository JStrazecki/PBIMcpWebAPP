"""
HTTP-to-MCP Bridge Server for Azure Web App
Provides HTTP endpoints that internally use MCP tools for Claude.ai Enterprise
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp-bridge")

try:
    from flask import Flask, jsonify, request, session, redirect, url_for, Response
    from flask_cors import CORS
    from mcp.server.fastmcp import FastMCP
    import requests
    import msal
    import jwt
    logger.info("All required libraries imported successfully")
except ImportError as e:
    logger.error(f"Failed to import required libraries: {e}")
    raise

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production')
CORS(app)

# Request logging middleware
@app.before_request
def log_request_info():
    """Log all incoming requests to help debug 405 errors"""
    logger.info(f"Request: {request.method} {request.url} from {request.remote_addr or 'unknown'}")

# Handle CORS preflight requests to reduce 405 errors
@app.before_request
def handle_preflight():
    """Handle OPTIONS requests for CORS preflight"""
    if request.method == "OPTIONS":
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        logger.info(f"CORS preflight handled for {request.url}")
        return response

# Initialize MCP server internally
mcp = FastMCP("powerbi-financial-server")

# OAuth 2.0 Configuration
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
TENANT_ID = os.environ.get('AZURE_TENANT_ID')
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'https://pbimcp.azurewebsites.net/auth/callback')

# Power BI OAuth scopes - for client credentials flow, use /.default
SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]

# MSAL Confidential Client
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
    logger.warning("OAuth not configured")

async def get_client_credentials_token() -> Optional[str]:
    """Get application-level token using client credentials flow"""
    if not msal_app:
        logger.error("MSAL app not configured")
        return None
    
    try:
        result = msal_app.acquire_token_for_client(scopes=SCOPES)
        
        if "access_token" in result:
            logger.info("Successfully acquired Power BI token")
            return result["access_token"]
        else:
            error_desc = result.get('error_description', 'Unknown error')
            logger.error(f"Failed to acquire Power BI token: {error_desc}")
            return None
            
    except Exception as e:
        logger.error(f"Error in client credentials flow: {e}")
        return None

# Define MCP tools as async functions
@mcp.tool()
async def get_powerbi_status() -> Dict[str, Any]:
    """Get Power BI authentication and server status"""
    token = await get_client_credentials_token()
    
    return {
        "server_status": "running",
        "powerbi_access": "granted" if token else "denied",
        "authentication": "client_credentials",
        "service": "Power BI MCP Finance Server",
        "version": "3.0.0-bridge",
        "timestamp": datetime.utcnow().isoformat()
    }

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check for the MCP server"""
    token = await get_client_credentials_token()
    
    return {
        "status": "healthy",
        "service": "Power BI MCP Finance Server",
        "version": "3.0.0-bridge",
        "protocol": "http_mcp_bridge",
        "environment": "azure" if os.environ.get('WEBSITE_HOSTNAME') else "local",
        "authentication": {
            "type": "client_credentials",
            "configured": bool(msal_app),
            "powerbi_access": bool(token)
        },
        "features": {
            "powerbi_integration": True,
            "mcp_tools": True,
            "http_bridge": True
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@mcp.tool() 
async def list_powerbi_workspaces() -> Dict[str, Any]:
    """List Power BI workspaces accessible with client credentials"""
    token = await get_client_credentials_token()
    
    if not token:
        return {
            "error": "Unable to access Power BI",
            "message": "Failed to acquire Power BI access token"
        }
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
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
                "workspaces": formatted_workspaces,
                "total_count": len(formatted_workspaces),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "error": f"Power BI API error: {response.status_code}",
                "message": response.text[:500]
            }
            
    except Exception as e:
        return {
            "error": f"Failed to retrieve workspaces: {str(e)}"
        }

@mcp.tool()
async def get_powerbi_datasets(workspace_id: Optional[str] = None) -> Dict[str, Any]:
    """Get Power BI datasets from workspaces"""
    token = await get_client_credentials_token()
    
    if not token:
        return {
            "error": "Unable to access Power BI",
            "message": "Failed to acquire Power BI access token"
        }
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if workspace_id:
            url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
        else:
            url = "https://api.powerbi.com/v1.0/myorg/datasets"
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            datasets_data = response.json()
            datasets = datasets_data.get("value", [])
            
            formatted_datasets = []
            for ds in datasets:
                formatted_datasets.append({
                    "id": ds["id"],
                    "name": ds["name"],
                    "web_url": ds.get("webUrl"),
                    "configured_by": ds.get("configuredBy"),
                    "is_refreshable": ds.get("isRefreshable", False),
                    "created_date": ds.get("createdDate"),
                    "content_provider_type": ds.get("contentProviderType")
                })
            
            return {
                "workspace_id": workspace_id or "all_accessible",
                "datasets": formatted_datasets,
                "total_count": len(formatted_datasets),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "error": f"Power BI API error: {response.status_code}",
                "message": response.text[:500]
            }
            
    except Exception as e:
        return {
            "error": f"Failed to retrieve datasets: {str(e)}"
        }

@mcp.tool()
async def execute_powerbi_query(dataset_id: str, dax_query: str, workspace_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute DAX query against Power BI dataset"""
    token = await get_client_credentials_token()
    
    if not token:
        return {
            "error": "Unable to access Power BI",
            "message": "Failed to acquire Power BI access token"
        }
    
    if not dataset_id or not dax_query:
        return {
            "error": "Missing required parameters",
            "required": "dataset_id and dax_query are required"
        }
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if workspace_id:
            url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
        else:
            url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/executeQueries"
        
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
            timeout=120
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            return {
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
                "status": "failed"
            }
            
    except Exception as e:
        return {
            "error": f"Failed to execute query: {str(e)}",
            "query": dax_query
        }

# HTTP endpoints that call MCP tools
async def call_mcp_tool(tool_name: str, **kwargs):
    """Helper function to call MCP tools asynchronously"""
    try:
        if tool_name == "get_powerbi_status":
            return await get_powerbi_status()
        elif tool_name == "health_check":
            return await health_check()
        elif tool_name == "list_powerbi_workspaces":
            return await list_powerbi_workspaces()
        elif tool_name == "get_powerbi_datasets":
            return await get_powerbi_datasets(kwargs.get('workspace_id'))
        elif tool_name == "execute_powerbi_query":
            return await execute_powerbi_query(
                kwargs.get('dataset_id'),
                kwargs.get('dax_query'),
                kwargs.get('workspace_id')
            )
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}

@app.route('/')
def index():
    """Root endpoint with MCP bridge information"""
    return jsonify({
        "service": "Power BI MCP Bridge Server",
        "status": "running",
        "version": "3.0.0-bridge",
        "protocol": "http_mcp_bridge",
        "authentication": {
            "type": "client_credentials",
            "configured": bool(msal_app)
        },
        "mcp_tools": [
            "get_powerbi_status",
            "health_check", 
            "list_powerbi_workspaces",
            "get_powerbi_datasets",
            "execute_powerbi_query"
        ],
        "endpoints": {
            "health": "/health",
            "mcp_status": "/mcp/status",
            "mcp_workspaces": "/mcp/workspaces",
            "mcp_datasets": "/mcp/datasets",
            "mcp_query": "/mcp/query",
            "mcp_discovery": "/.well-known/mcp"
        },
        "features": {
            "powerbi_integration": True,
            "mcp_bridge": True,
            "async_tools": True
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/.well-known/mcp')
def mcp_discovery():
    """MCP discovery endpoint for Claude.ai"""
    base_url = request.base_url.replace('/.well-known/mcp', '')
    
    return jsonify({
        "version": "2024-11-05",
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False,
            "logging": True
        },
        "serverInfo": {
            "name": "powerbi-mcp-bridge",
            "version": "3.0.0-bridge"
        },
        "authentication": {
            "type": "oauth2",
            "authorization_url": f"{base_url}/authorize",
            "token_url": f"{base_url}/token",
            "scopes": ["powerbi"]
        }
    })

@app.route('/token', methods=['POST'])
def token_endpoint():
    """OAuth token endpoint for Claude.ai MCP integration"""
    if not msal_app:
        return jsonify({
            "error": "invalid_client",
            "error_description": "OAuth not configured on server"
        }), 400
    
    # Get token request parameters
    grant_type = request.form.get('grant_type')
    code = request.form.get('code')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    redirect_uri = request.form.get('redirect_uri')
    
    logger.info(f"Token request: grant_type={grant_type}, client_id={client_id}")
    
    if grant_type != 'authorization_code':
        return jsonify({
            "error": "unsupported_grant_type",
            "error_description": "Only authorization_code grant type is supported"
        }), 400
    
    if not code:
        return jsonify({
            "error": "invalid_request",
            "error_description": "Missing authorization code"
        }), 400
    
    # For Claude.ai, validate against configured client credentials
    if client_id != CLIENT_ID or client_secret != CLIENT_SECRET:
        logger.warning(f"Invalid client credentials from Claude: {client_id}")
        return jsonify({
            "error": "invalid_client",
            "error_description": "Invalid client credentials"
        }), 401
    
    try:
        # Generate access token for Claude.ai
        import secrets
        access_token = secrets.token_urlsafe(64)
        
        logger.info(f"Generated access token for Claude client: {client_id}")
        
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "scope": "powerbi"
        })
        
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        return jsonify({
            "error": "server_error",
            "error_description": f"Failed to generate token: {str(e)}"
        }), 500

@app.route('/authorize')
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

@app.route('/auth/callback')
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
            # Check if this is a Claude.ai callback
            original_redirect_uri = session.get('claude_redirect_uri')
            if original_redirect_uri and 'claude.ai' in original_redirect_uri:
                # Forward to Claude.ai with authorization code
                claude_callback_url = f"{original_redirect_uri}?code={code}&state={request.args.get('state', '')}"
                return redirect(claude_callback_url)
            
            # Regular callback - return success
            return jsonify({
                "status": "authenticated",
                "message": "Authentication successful!",
                "access_token": result["access_token"][:50] + "...",  # Truncated for security
                "token_type": "Bearer"
            })
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

@app.route('/health')
def health():
    """Health check endpoint"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(call_mcp_tool("health_check"))
        return jsonify(result)
    finally:
        loop.close()

@app.route('/mcp/status')
def mcp_status():
    """MCP status endpoint"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(call_mcp_tool("get_powerbi_status"))
        return jsonify(result)
    finally:
        loop.close()

@app.route('/mcp/workspaces')
def mcp_workspaces():
    """MCP workspaces endpoint"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(call_mcp_tool("list_powerbi_workspaces"))
        return jsonify(result)
    finally:
        loop.close()

@app.route('/mcp/datasets')
def mcp_datasets():
    """MCP datasets endpoint"""
    workspace_id = request.args.get('workspace_id')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(call_mcp_tool("get_powerbi_datasets", workspace_id=workspace_id))
        return jsonify(result)
    finally:
        loop.close()

@app.route('/mcp/query', methods=['POST'])
def mcp_query():
    """MCP query endpoint"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON payload required"}), 400
    
    dataset_id = data.get('dataset_id')
    dax_query = data.get('dax_query')
    workspace_id = data.get('workspace_id')
    
    # Input validation
    if not dataset_id or not isinstance(dataset_id, str):
        return jsonify({"error": "dataset_id is required and must be a string"}), 400
    
    if not dax_query or not isinstance(dax_query, str):
        return jsonify({"error": "dax_query is required and must be a string"}), 400
    
    if len(dax_query) > 10000:  # Reasonable limit for DAX queries
        return jsonify({"error": "dax_query is too long (max 10000 characters)"}), 400
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(call_mcp_tool(
            "execute_powerbi_query",
            dataset_id=dataset_id,
            dax_query=dax_query,
            workspace_id=workspace_id
        ))
        return jsonify(result)
    finally:
        loop.close()

# MCP Protocol Endpoints for Claude.ai
@app.route('/mcp/initialize', methods=['POST'])
def mcp_initialize():
    """MCP protocol initialize endpoint"""
    return jsonify({
        "jsonrpc": "2.0",
        "id": request.json.get('id') if request.json else 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "logging": {}
            },
            "serverInfo": {
                "name": "powerbi-mcp-bridge",
                "version": "3.0.0-bridge"
            }
        }
    })

@app.route('/mcp/tools/list', methods=['POST'])
def mcp_tools_list():
    """MCP protocol tools list endpoint"""
    tools = [
        {
            "name": "get_powerbi_status",
            "description": "Get Power BI server status and authentication info",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "list_powerbi_workspaces",
            "description": "List all accessible Power BI workspaces",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_powerbi_datasets",
            "description": "Get Power BI datasets from a workspace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "type": "string",
                        "description": "Optional workspace ID to filter datasets"
                    }
                },
                "required": []
            }
        },
        {
            "name": "execute_powerbi_query",
            "description": "Execute a DAX query against a Power BI dataset",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "dataset_id": {
                        "type": "string",
                        "description": "The Power BI dataset ID"
                    },
                    "dax_query": {
                        "type": "string",
                        "description": "The DAX query to execute"
                    },
                    "workspace_id": {
                        "type": "string",
                        "description": "Optional workspace ID"
                    }
                },
                "required": ["dataset_id", "dax_query"]
            }
        }
    ]
    
    return jsonify({
        "jsonrpc": "2.0",
        "id": request.json.get('id') if request.json else 1,
        "result": {
            "tools": tools
        }
    })

@app.route('/mcp/tools/call', methods=['POST'])
def mcp_tools_call():
    """MCP protocol tools call endpoint"""
    data = request.get_json()
    if not data:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        }), 400
    
    tool_name = data.get('params', {}).get('name')
    arguments = data.get('params', {}).get('arguments', {})
    request_id = data.get('id', 1)
    
    # Map MCP tool calls to our async functions
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if tool_name == "get_powerbi_status":
            result = loop.run_until_complete(call_mcp_tool("get_powerbi_status"))
        elif tool_name == "list_powerbi_workspaces":
            result = loop.run_until_complete(call_mcp_tool("list_powerbi_workspaces"))
        elif tool_name == "get_powerbi_datasets":
            result = loop.run_until_complete(call_mcp_tool("get_powerbi_datasets", **arguments))
        elif tool_name == "execute_powerbi_query":
            result = loop.run_until_complete(call_mcp_tool("execute_powerbi_query", **arguments))
        else:
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }), 400
        
        return jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        })
    finally:
        loop.close()

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors with detailed logging"""
    logger.warning(f"404 Error: {request.method} {request.url} from {request.remote_addr or 'unknown'}")
    return jsonify({
        "error": "Not Found",
        "message": f"The requested endpoint '{request.path}' was not found",
        "method": request.method,
        "url": str(request.url),
        "available_endpoints": [
            "/", "/health", "/mcp/status", "/mcp/workspaces", 
            "/mcp/datasets", "/authorize", "/auth/callback", "/mcp/query"
        ]
    }), 404

@app.errorhandler(405)
def method_not_allowed_error(error):
    """Handle 405 Method Not Allowed errors with detailed logging"""
    logger.warning(f"405 Error: {request.method} {request.url} from {request.remote_addr or 'unknown'} - Method not allowed")
    return jsonify({
        "error": "Method Not Allowed",
        "message": f"The method '{request.method}' is not allowed for endpoint '{request.path}'",
        "method": request.method,
        "url": str(request.url),
        "allowed_methods": ["GET", "POST", "OPTIONS"]
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "status": "error"
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle uncaught exceptions"""
    logger.error(f"Uncaught exception: {e}", exc_info=True)
    return jsonify({
        "error": "Unexpected Error",
        "message": str(e),
        "type": type(e).__name__
    }), 500

def create_app():
    """Create Flask app for Azure deployment"""
    return app

# For Azure deployment
APP = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting MCP Bridge Server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)