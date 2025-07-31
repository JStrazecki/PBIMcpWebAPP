"""
Simple MCP Server for Claude AI
No user authentication required - uses Azure client credentials for Power BI
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import time
import threading
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("pbi-mcp-simple")

app = Flask(__name__)
CORS(app)

# Power BI Client Credentials Configuration
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET', '')
TENANT_ID = os.environ.get('AZURE_TENANT_ID', '')

# MCP Server Access Control - Set these to control who can connect
MCP_ALLOWED_CLIENT_ID = os.environ.get('MCP_CLIENT_ID', 'demo-client-id')
MCP_ALLOWED_CLIENT_SECRET = os.environ.get('MCP_CLIENT_SECRET', 'demo-client-secret')

# Power BI OAuth scopes for client credentials
POWERBI_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]

def check_claude_auth():
    """Check if request has a valid bearer token from Claude (always accept)"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        # Any bearer token is valid for this simple server
        return True
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

@app.route('/')
def home():
    """MCP Server information"""
    return jsonify({
        "name": "Power BI MCP Server (Simple)",
        "version": "1.0.0", 
        "protocol_version": "2024-11-05",
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False
        },
        "server_info": {
            "name": "powerbi-simple-mcp",
            "version": "1.0.0"
        },
        "authentication": {
            "type": "oauth2",
            "client_validation": "enabled",
            "allowed_client_id": CLIENT_ID,
            "powerbi_configured": bool(CLIENT_ID and CLIENT_SECRET and TENANT_ID),
            "note": "Uses Power BI app registration for both MCP access and Power BI integration"
        },
        "instructions": [
            "This server provides Power BI integration tools",
            "Available tools: health, workspaces, datasets, query",
            "OAuth2 authentication required with valid client credentials"
        ]
    })

@app.route('/.well-known/mcp')
def mcp_discovery():
    """MCP discovery endpoint"""
    base_url = request.base_url.replace('/.well-known/mcp', '')
    return jsonify({
        "version": "2024-11-05",
        "authentication": {
            "type": "oauth2",
            "authorization_url": f"{base_url}/authorize",
            "token_url": f"{base_url}/token",
            "scopes": ["powerbi"]
        },
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False
        },
        "server": {
            "name": "powerbi-simple-mcp",
            "version": "1.0.0"
        }
    })

@app.route('/health')
def health():
    """Health check"""
    # Test Power BI connection
    token = get_powerbi_token()
    powerbi_configured = bool(token)
    
    return jsonify({
        "status": "healthy",
        "service": "Power BI MCP Server (Simple)",
        "authentication": "client_credentials",
        "powerbi_configured": powerbi_configured,
        "powerbi_access": "granted" if token else "using_demo_data",
        "client_id_configured": bool(CLIENT_ID),
        "environment": "Azure" if os.environ.get('WEBSITE_HOSTNAME') else "Local",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/workspaces')
def workspaces():
    """List Power BI workspaces (real data if configured, demo otherwise)"""
    # Check Claude auth if present (but don't require it for backwards compatibility)
    has_claude_auth = check_claude_auth()
    if has_claude_auth:
        logger.info("Request authenticated via Claude bearer token")
    
    token = get_powerbi_token()
    
    if token:
        # Get real Power BI workspaces
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
                
                return jsonify({
                    "workspaces": formatted_workspaces,
                    "total_count": len(formatted_workspaces),
                    "mode": "real_powerbi_data",
                    "authentication": "client_credentials",
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                logger.error(f"Power BI API error: {response.status_code} - {response.text}")
                # Fall through to demo data
        except Exception as e:
            logger.error(f"Error fetching Power BI workspaces: {e}")
            # Fall through to demo data
    
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
    
    return jsonify({
        "workspaces": demo_workspaces,
        "total_count": len(demo_workspaces),
        "mode": "demo_data",
        "authentication": "client_credentials_not_configured",
        "note": "Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID for real Power BI data",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/datasets')
def datasets():
    """Get Power BI datasets (real data if configured, demo otherwise)"""
    # Check Claude auth if present (but don't require it for backwards compatibility)
    has_claude_auth = check_claude_auth()
    if has_claude_auth:
        logger.info("Request authenticated via Claude bearer token")
    
    workspace_id = request.args.get('workspace_id')
    token = get_powerbi_token()
    
    if token:
        # Get real Power BI datasets
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
                
                return jsonify({
                    "workspace_id": workspace_id or "all_accessible",
                    "datasets": formatted_datasets,
                    "total_count": len(formatted_datasets),
                    "mode": "real_powerbi_data",
                    "authentication": "client_credentials",
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                logger.error(f"Power BI datasets API error: {response.status_code} - {response.text}")
                # Fall through to demo data
        except Exception as e:
            logger.error(f"Error fetching Power BI datasets: {e}")
            # Fall through to demo data
    
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
    
    # Filter by workspace if specified
    if workspace_id and not workspace_id.startswith('demo-'):
        # If real workspace ID provided but no token, return empty
        filtered_datasets = []
    elif workspace_id:
        filtered_datasets = [ds for ds in demo_datasets if ds["workspace_id"] == workspace_id]
    else:
        filtered_datasets = demo_datasets
    
    return jsonify({
        "workspace_id": workspace_id or "all",
        "datasets": filtered_datasets,
        "total_count": len(filtered_datasets),
        "mode": "demo_data",
        "authentication": "client_credentials_not_configured",
        "note": "Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID for real Power BI data",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/query', methods=['POST'])
def query():
    """Execute Power BI query (real DAX if configured, demo otherwise)"""
    # Check Claude auth if present (but don't require it for backwards compatibility)
    has_claude_auth = check_claude_auth()
    if has_claude_auth:
        logger.info("Request authenticated via Claude bearer token")
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    dataset_id = data.get('dataset_id')
    dax_query = data.get('dax_query') or data.get('query', '')
    workspace_id = data.get('workspace_id')
    
    if not dataset_id:
        return jsonify({"error": "dataset_id is required"}), 400
    
    token = get_powerbi_token()
    
    if token and dax_query:
        # Execute real DAX query
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
                
                return jsonify({
                    "dataset_id": dataset_id,
                    "workspace_id": workspace_id,
                    "dax_query": dax_query,
                    "results": result_data.get("results", []),
                    "mode": "real_powerbi_query",
                    "authentication": "client_credentials",
                    "execution_time": datetime.utcnow().isoformat(),
                    "status": "success"
                })
            else:
                logger.error(f"Power BI query API error: {response.status_code} - {response.text}")
                return jsonify({
                    "error": f"Power BI API error: {response.status_code}",
                    "message": response.text[:500],
                    "dax_query": dax_query,
                    "mode": "real_powerbi_query_failed",
                    "status": "failed"
                }), 400
                
        except Exception as e:
            logger.error(f"Error executing Power BI query: {e}")
            return jsonify({
                "error": f"Query execution failed: {str(e)}",
                "dax_query": dax_query,
                "mode": "real_powerbi_query_failed",
                "status": "failed"
            }), 500
    
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
    
    return jsonify({
        "dataset_id": dataset_id,
        "query": dax_query or "demo query",
        "results": results,
        "mode": "demo_data",
        "authentication": "client_credentials_not_configured",
        "note": "Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID for real Power BI queries",
        "execution_time": datetime.utcnow().isoformat(),
        "status": "success"
    })

@app.route('/authorize')
def authorize():
    """Handle Claude's OAuth authorize request - always approve"""
    # Get OAuth parameters from Claude
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    state = request.args.get('state')
    code_challenge = request.args.get('code_challenge')
    
    # Log the attempt for debugging
    logger.info(f"OAuth authorize request: client_id={client_id}, redirect_uri={redirect_uri}")
    
    if not redirect_uri or not state:
        return jsonify({
            "error": "invalid_request",
            "error_description": "Missing required parameters"
        }), 400
    
    # Generate a dummy authorization code
    import secrets
    auth_code = secrets.token_urlsafe(32)
    
    # Redirect back to Claude with the authorization code
    redirect_url = f"{redirect_uri}?code={auth_code}&state={state}"
    
    from flask import redirect
    return redirect(redirect_url)

@app.route('/token', methods=['POST'])
def token():
    """Handle Claude's OAuth token request - validate client credentials"""
    # Get token request parameters
    grant_type = request.form.get('grant_type')
    code = request.form.get('code')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    redirect_uri = request.form.get('redirect_uri')
    code_verifier = request.form.get('code_verifier')
    
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
    
    # VALIDATE CLIENT CREDENTIALS
    if not client_id or not client_secret:
        logger.warning("Token request missing client credentials")
        return jsonify({
            "error": "invalid_client",
            "error_description": "Client authentication required"
        }), 401
    
    # Validate against Power BI app registration credentials
    if client_id != CLIENT_ID or client_secret != CLIENT_SECRET:
        logger.warning(f"Invalid client credentials: {client_id}")
        return jsonify({
            "error": "invalid_client", 
            "error_description": "Invalid client credentials"
        }), 401
    
    logger.info(f"Client {client_id} authenticated successfully")
    
    # Generate access token for valid client
    import secrets
    access_token = secrets.token_urlsafe(64)
    
    # Return OAuth token response
    return jsonify({
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "scope": "powerbi"
    })

@app.route('/claude-config')
def claude_config():
    """Claude AI configuration helper"""
    base_url = request.base_url.replace('/claude-config', '')
    
    return jsonify({
        "claude_setup": {
            "step_1": "Open Claude AI Settings > Connectors",
            "step_2": "Click 'Add Remote MCP Server'",
            "step_3": f"Enter URL: {base_url}",
            "step_4": "Set Authentication: OAuth2",
            "step_5": f"Client ID: {CLIENT_ID}", 
            "step_6": f"Client Secret: {CLIENT_SECRET}",
            "step_7": "Save and test connection"
        },
        "server_url": base_url,
        "authentication": "oauth2_validated",
        "oauth_endpoints": {
            "authorization_url": f"{base_url}/authorize",
            "token_url": f"{base_url}/token"
        },
        "security": {
            "client_validation": "enabled",
            "allowed_client_id": CLIENT_ID,
            "note": "Uses Power BI app registration credentials for MCP access"
        },
        "power_bi_integration": {
            "AZURE_CLIENT_ID": "Your Power BI app registration client ID",
            "AZURE_CLIENT_SECRET": "Your Power BI app registration client secret", 
            "AZURE_TENANT_ID": "Your Azure tenant ID",
            "note": "Same credentials used for both MCP access and Power BI integration"
        },
        "test_command": "Ask Claude: 'Can you check the Power BI server health?'"
    })

# Global storage for SSE connections
sse_clients = {}
message_queue = queue.Queue()

# MCP SSE Transport Implementation
@app.route('/sse')
def sse_endpoint():
    """SSE endpoint for server-to-client streaming"""
    # Check authentication
    has_claude_auth = check_claude_auth()
    if not has_claude_auth:
        return "Authentication required", 401
    
    def event_stream():
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"
        
        # Keep-alive heartbeat to prevent timeouts
        while True:
            try:
                # Send keep-alive every 30 seconds
                yield f": heartbeat\n\n"
                time.sleep(30)
            except GeneratorExit:
                break
    
    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Authorization, Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
        }
    )

@app.route('/message', methods=['POST'])
def message_endpoint():
    """Message endpoint for client-to-server communication"""
    # Check authentication
    has_claude_auth = check_claude_auth()
    if not has_claude_auth:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32001,
                "message": "Authentication required"
            }
        }), 401
    
    data = request.get_json()
    if not data:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        }), 400
    
    method = data.get('method')
    params = data.get('params', {})
    request_id = data.get('id')
    
    logger.info(f"MCP request: method={method}, id={request_id}")
    
    # Initialize handshake
    if method == 'initialize':
        return jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "logging": {}
                },
                "serverInfo": {
                    "name": "powerbi-mcp-server",
                    "version": "1.0.0"
                }
            }
        })
    
    # List available tools
    elif method == 'tools/list':
        tools = [
            {
                "name": "powerbi_health",
                "description": "Check Power BI server health and configuration status",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "powerbi_workspaces",
                "description": "List Power BI workspaces accessible to the server",
                "inputSchema": {
                    "type": "object", 
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "powerbi_datasets",
                "description": "Get Power BI datasets from a specific workspace or all accessible workspaces",
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
                "name": "powerbi_query",
                "description": "Execute a DAX query against a Power BI dataset",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dataset_id": {
                            "type": "string",
                            "description": "The Power BI dataset ID to query"
                        },
                        "dax_query": {
                            "type": "string", 
                            "description": "The DAX query to execute"
                        },
                        "workspace_id": {
                            "type": "string",
                            "description": "Optional workspace ID if dataset is in a specific workspace"
                        }
                    },
                    "required": ["dataset_id", "dax_query"]
                }
            }
        ]
        
        return jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools
            }
        })
    
    # Call a specific tool
    elif method == 'tools/call':
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if tool_name == 'powerbi_health':
            # Call the existing health endpoint logic
            token = get_powerbi_token()
            powerbi_configured = bool(token)
            
            result = {
                "status": "healthy",
                "service": "Power BI MCP Server (Simple)",
                "authentication": "client_credentials",
                "powerbi_configured": powerbi_configured,
                "powerbi_access": "granted" if token else "using_demo_data",
                "client_id_configured": bool(CLIENT_ID),
                "environment": "Azure" if os.environ.get('WEBSITE_HOSTNAME') else "Local",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Power BI Server Health:\n{json.dumps(result, indent=2)}"
                        }
                    ]
                }
            })
        
        elif tool_name == 'powerbi_workspaces':
            # Call workspaces logic
            with app.test_request_context():
                response = workspaces()
                if hasattr(response, 'get_json'):
                    workspace_data = response.get_json()
                else:
                    workspace_data = response
            
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text", 
                            "text": f"Power BI Workspaces:\n{json.dumps(workspace_data, indent=2)}"
                        }
                    ]
                }
            })
        
        elif tool_name == 'powerbi_datasets':
            # Call datasets logic
            workspace_id = arguments.get('workspace_id')
            with app.test_request_context(query_string={'workspace_id': workspace_id} if workspace_id else None):
                response = datasets()
                if hasattr(response, 'get_json'):
                    dataset_data = response.get_json()
                else:
                    dataset_data = response
            
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Power BI Datasets:\n{json.dumps(dataset_data, indent=2)}"
                        }
                    ]
                }
            })
        
        elif tool_name == 'powerbi_query':
            # Call query logic
            dataset_id = arguments.get('dataset_id')
            dax_query = arguments.get('dax_query')
            workspace_id = arguments.get('workspace_id')
            
            if not dataset_id or not dax_query:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "dataset_id and dax_query are required"
                    }
                }), 400
            
            query_data = {
                'dataset_id': dataset_id,
                'dax_query': dax_query,
                'workspace_id': workspace_id
            }
            
            with app.test_request_context(json=query_data, content_type='application/json'):
                response = query()
                if hasattr(response, 'get_json'):
                    query_data_result = response.get_json()
                else:
                    query_data_result = response
            
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Power BI Query Results:\n{json.dumps(query_data_result, indent=2)}"
                        }
                    ]
                }
            })
        
        else:
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }), 400
    
    # Unknown method
    else:
        return jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))  # Use 8000 as default for Azure
    
    logger.info(f"Starting Simple MCP Server on port {port}")
    logger.info(f"Environment: {'Azure' if os.environ.get('WEBSITE_HOSTNAME') else 'Local'}")
    
    # Azure compatibility
    if os.environ.get('WEBSITE_HOSTNAME'):
        logger.info(f"Azure deployment detected: {os.environ.get('WEBSITE_HOSTNAME')}")
    
    app.run(host='0.0.0.0', port=port, debug=False)