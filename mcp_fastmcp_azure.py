"""
Power BI MCP Server using FastMCP with OAuth2 support for Azure
Combines FastMCP with Flask for OAuth2 endpoints
"""

import os
import sys
import logging
import json
import secrets
from typing import Optional, Dict, Any
from datetime import datetime

from flask import Flask, request, jsonify, redirect, Response
from flask_cors import CORS
from fastmcp import FastMCP
from fastmcp.server import Context
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("pbi-fastmcp-azure")

# Power BI Client Credentials Configuration
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET', '')
TENANT_ID = os.environ.get('AZURE_TENANT_ID', '')

# Create Flask app for OAuth2 endpoints
flask_app = Flask(__name__)
CORS(flask_app)

# Create FastMCP server
mcp = FastMCP(
    "Power BI MCP Server",
    version="3.0.0",
    description="Power BI integration via Model Context Protocol with FastMCP"
)

# Power BI OAuth scopes
POWERBI_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]

def check_claude_auth():
    """Check if request has a valid bearer token from Claude"""
    auth_header = request.headers.get('Authorization')
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    logger.info(f"Auth check - User-Agent: {user_agent}, Auth header: {auth_header[:30] if auth_header else 'None'}...")
    
    if auth_header:
        if (auth_header.startswith('Bearer ') or 
            auth_header.startswith('bearer ') or
            'Bearer Bearer' in auth_header):
            logger.info(f"Valid auth header detected from {user_agent}")
            return True
    logger.warning(f"Invalid or missing auth header from {user_agent}: {auth_header}")
    return False

def get_powerbi_token() -> Optional[str]:
    """Get Power BI access token using client credentials flow"""
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        logger.warning("Power BI client credentials not configured - using demo data")
        return None
    
    try:
        token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
        
        token_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': ' '.join(POWERBI_SCOPES),
            'grant_type': 'client_credentials'
        }
        
        response = requests.post(token_url, data=token_data, timeout=30)
        
        if response.status_code == 200:
            token_info = response.json()
            logger.info("Successfully acquired Power BI access token")
            return token_info.get('access_token')
        else:
            logger.error(f"Failed to get Power BI token: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting Power BI token: {e}")
        return None

# Flask OAuth2 endpoints
@flask_app.route('/', methods=['GET', 'POST'])
def home():
    """Root endpoint for server info"""
    base_url = request.base_url
    if 'azurewebsites.net' in base_url:
        base_url = base_url.replace('http://', 'https://')
    
    return jsonify({
        "name": "Power BI MCP Server (FastMCP)",
        "version": "3.0.0", 
        "protocol_version": "2024-11-05",
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False
        },
        "server_info": {
            "name": "powerbi-fastmcp",
            "version": "3.0.0"
        },
        "authentication": {
            "type": "oauth2",
            "powerbi_configured": bool(CLIENT_ID and CLIENT_SECRET and TENANT_ID),
        },
        "endpoints": {
            "mcp": f"{base_url}mcp",
            "oauth_authorize": f"{base_url}authorize",
            "oauth_token": f"{base_url}token",
            "health": f"{base_url}health"
        }
    })

@flask_app.route('/health')
def health():
    """Health check endpoint"""
    token = get_powerbi_token()
    powerbi_configured = bool(token)
    
    return jsonify({
        "status": "healthy",
        "service": "Power BI MCP Server (FastMCP)",
        "version": "3.0.0",
        "authentication": "client_credentials",
        "powerbi_configured": powerbi_configured,
        "powerbi_access": "granted" if token else "using_demo_data",
        "client_id_configured": bool(CLIENT_ID),
        "environment": "Azure" if os.environ.get('WEBSITE_HOSTNAME') else "Local",
        "framework": "FastMCP + Flask",
        "timestamp": datetime.utcnow().isoformat()
    })

@flask_app.route('/authorize', methods=['GET', 'POST'])
def authorize():
    """Handle Claude's OAuth authorize request"""
    if request.method == 'POST':
        data = request.get_json() or request.form
        client_id = data.get('client_id')
        redirect_uri = data.get('redirect_uri')
        state = data.get('state')
    else:
        client_id = request.args.get('client_id')
        redirect_uri = request.args.get('redirect_uri')
        state = request.args.get('state')
    
    logger.info(f"OAuth authorize request: method={request.method}, client_id={client_id}, redirect_uri={redirect_uri}")
    
    if not redirect_uri:
        redirect_uri = "https://claude.ai/api/mcp/auth_callback"
        logger.info(f"Using default redirect URI: {redirect_uri}")
    
    if not state:
        state = "claude-auth-state"
        logger.info(f"Using default state: {state}")
    
    auth_code = secrets.token_urlsafe(32)
    logger.info(f"Generated auth code for client_id={client_id}")
    
    redirect_url = f"{redirect_uri}?code={auth_code}&state={state}"
    return redirect(redirect_url)

@flask_app.route('/token', methods=['POST'])
def token():
    """Handle Claude's OAuth token request"""
    grant_type = request.form.get('grant_type')
    code = request.form.get('code')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    
    logger.info(f"OAuth token request: grant_type={grant_type}, client_id={client_id}")
    
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
    
    # Validate client credentials
    if not client_id or not client_secret:
        logger.warning("Token request missing client credentials")
        return jsonify({
            "error": "invalid_client",
            "error_description": "Client authentication required"
        }), 401
    
    if client_id != CLIENT_ID or client_secret != CLIENT_SECRET:
        logger.warning(f"Invalid client credentials: client_id='{client_id}'")
        return jsonify({
            "error": "invalid_client", 
            "error_description": "Invalid client credentials"
        }), 401
    
    logger.info(f"Client {client_id} authenticated successfully")
    
    access_token = secrets.token_urlsafe(64)
    
    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "powerbi"
    })

# CORS preflight handlers
@flask_app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    """Handle CORS preflight requests"""
    response = Response('', 200)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

# FastMCP tools
@mcp.tool()
async def powerbi_health(ctx: Context) -> str:
    """Check Power BI server health and configuration status"""
    token = get_powerbi_token()
    powerbi_configured = bool(token)
    
    result = {
        "status": "healthy",
        "service": "Power BI MCP Server (FastMCP)",
        "version": "3.0.0",
        "authentication": "client_credentials",
        "powerbi_configured": powerbi_configured,
        "powerbi_access": "granted" if token else "using_demo_data",
        "client_id_configured": bool(CLIENT_ID),
        "environment": "Azure" if os.environ.get('WEBSITE_HOSTNAME') else "Local",
        "framework": "FastMCP",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def powerbi_workspaces(ctx: Context) -> str:
    """List Power BI workspaces accessible to the server"""
    token = get_powerbi_token()
    
    if token:
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
                
                result = {
                    "workspaces": formatted_workspaces,
                    "total_count": len(formatted_workspaces),
                    "mode": "real_powerbi_data",
                    "authentication": "client_credentials",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error fetching Power BI workspaces: {e}")
    
    # Demo data fallback
    demo_workspaces = [
        {
            "id": "demo-ws-1",
            "name": "Finance Dashboard",
            "type": "Workspace",
            "state": "Active",
            "datasets_count": 3
        },
        {
            "id": "demo-ws-2", 
            "name": "Sales Reports",
            "type": "Workspace",
            "state": "Active",
            "datasets_count": 5
        },
        {
            "id": "demo-ws-3",
            "name": "Operations Analytics",
            "type": "Workspace",
            "state": "Active",
            "datasets_count": 2
        }
    ]
    
    result = {
        "workspaces": demo_workspaces,
        "total_count": len(demo_workspaces),
        "mode": "demo_data",
        "authentication": "client_credentials_not_configured",
        "note": "Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID for real Power BI data",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def powerbi_datasets(ctx: Context, workspace_id: Optional[str] = None) -> str:
    """Get Power BI datasets from a specific workspace or all accessible workspaces
    
    Args:
        workspace_id: Optional workspace ID to filter datasets
    """
    token = get_powerbi_token()
    
    if token:
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
                
                result = {
                    "workspace_id": workspace_id or "all_accessible",
                    "datasets": formatted_datasets,
                    "total_count": len(formatted_datasets),
                    "mode": "real_powerbi_data",
                    "authentication": "client_credentials",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error fetching Power BI datasets: {e}")
    
    # Demo data fallback
    demo_datasets = [
        {
            "id": "demo-ds-1",
            "name": "Financial KPIs",
            "workspace_id": "demo-ws-1",
            "is_refreshable": True,
            "tables": ["Revenue", "Expenses", "Profit"]
        },
        {
            "id": "demo-ds-2",
            "name": "Sales Performance", 
            "workspace_id": "demo-ws-2",
            "is_refreshable": True,
            "tables": ["Sales", "Customers", "Products"]
        },
        {
            "id": "demo-ds-3",
            "name": "Operations Metrics",
            "workspace_id": "demo-ws-3",
            "is_refreshable": False,
            "tables": ["Inventory", "Orders", "Deliveries"]
        }
    ]
    
    if workspace_id and not workspace_id.startswith('demo-'):
        filtered_datasets = []
    elif workspace_id:
        filtered_datasets = [ds for ds in demo_datasets if ds["workspace_id"] == workspace_id]
    else:
        filtered_datasets = demo_datasets
    
    result = {
        "workspace_id": workspace_id or "all",
        "datasets": filtered_datasets,
        "total_count": len(filtered_datasets),
        "mode": "demo_data",
        "authentication": "client_credentials_not_configured",
        "note": "Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID for real Power BI data",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def powerbi_query(
    ctx: Context,
    dataset_id: str,
    dax_query: str,
    workspace_id: Optional[str] = None
) -> str:
    """Execute a DAX query against a Power BI dataset
    
    Args:
        dataset_id: The Power BI dataset ID to query
        dax_query: The DAX query to execute
        workspace_id: Optional workspace ID if dataset is in a specific workspace
    """
    token = get_powerbi_token()
    
    if token and dax_query:
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
                
                result = {
                    "dataset_id": dataset_id,
                    "workspace_id": workspace_id,
                    "dax_query": dax_query,
                    "results": result_data.get("results", []),
                    "mode": "real_powerbi_query",
                    "authentication": "client_credentials",
                    "execution_time": datetime.utcnow().isoformat(),
                    "status": "success"
                }
                
                return json.dumps(result, indent=2)
            else:
                error_message = response.text[:500]
                troubleshooting_tip = ""
                
                if "MSOLAP connection" in error_message or "DatasetExecuteQueriesError" in error_message:
                    troubleshooting_tip = "Your service principal needs to be added as a Member (not Viewer) to the Power BI workspace."
                elif response.status_code == 403:
                    troubleshooting_tip = "Your service principal needs 'Dataset.Read.All' API permissions and workspace Member access."
                elif response.status_code == 401:
                    troubleshooting_tip = "Check your AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID environment variables."
                
                return f"Power BI API error: {response.status_code}\n{error_message}\n\nTroubleshooting: {troubleshooting_tip}"
                
        except Exception as e:
            logger.error(f"Error executing Power BI query: {e}")
            return f"Query execution failed: {str(e)}"
    
    # Demo results fallback
    demo_results = {
        "demo-ds-1": [
            {"Metric": "Total Revenue", "Value": 1250000, "Period": "Q1 2024"},
            {"Metric": "Total Expenses", "Value": 850000, "Period": "Q1 2024"},
            {"Metric": "Net Profit", "Value": 400000, "Period": "Q1 2024"}
        ],
        "demo-ds-2": [
            {"Product": "Product A", "Sales": 45000, "Units": 150},
            {"Product": "Product B", "Sales": 32000, "Units": 95},
            {"Product": "Product C", "Sales": 67000, "Units": 220}
        ],
        "demo-ds-3": [
            {"Department": "Warehouse", "Orders": 1250, "Efficiency": "94%"},
            {"Department": "Shipping", "Orders": 1180, "Efficiency": "89%"},
            {"Department": "Returns", "Orders": 70, "Efficiency": "92%"}
        ]
    }
    
    results = demo_results.get(dataset_id, [{"Message": "No demo data for this dataset"}])
    
    result = {
        "dataset_id": dataset_id,
        "query": dax_query or "demo query",
        "results": results,
        "mode": "demo_data",
        "authentication": "client_credentials_not_configured",
        "note": "Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID for real Power BI queries",
        "execution_time": datetime.utcnow().isoformat(),
        "status": "success"
    }
    
    return json.dumps(result, indent=2)

# Initialization handler
@mcp.on_initialize
async def on_initialize(ctx: Context, params):
    """Handle initialization and log protocol details"""
    logger.info(f"FastMCP initialization - Protocol version: {params.get('protocolVersion', 'unknown')}")
    logger.info(f"Client info: {params.get('clientInfo', {})}")
    logger.info("FastMCP server ready with Power BI tools")

# Create combined ASGI app
def create_app():
    """Create the combined ASGI application"""
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.exceptions import NotFound
    
    # Get FastMCP ASGI app
    mcp_asgi = mcp.get_asgi_app(
        transport="http",
        path="/mcp"
    )
    
    # Convert Flask to ASGI using a2wsgi
    try:
        from a2wsgi import WSGIMiddleware
        flask_asgi = WSGIMiddleware(flask_app)
    except ImportError:
        logger.error("a2wsgi not installed. Install with: pip install a2wsgi")
        raise
    
    # Create dispatcher to route requests
    def dispatcher(environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path.startswith('/mcp'):
            # Route to FastMCP
            return mcp_asgi(environ, start_response)
        else:
            # Route to Flask for OAuth2 and other endpoints
            return flask_asgi(environ, start_response)
    
    return dispatcher

# ASGI application
application = create_app()

if __name__ == "__main__":
    # For local testing
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting FastMCP + Flask server on port {port}")
    uvicorn.run(application, host="0.0.0.0", port=port)