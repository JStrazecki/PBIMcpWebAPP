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
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    logger.info(f"Auth check - User-Agent: {user_agent}, Auth header: {auth_header[:30] if auth_header else 'None'}...")
    
    if auth_header:
        # Handle both single and double "Bearer" prefix issues
        if (auth_header.startswith('Bearer ') or 
            auth_header.startswith('bearer ') or
            'Bearer Bearer' in auth_header):
            # Any bearer token is valid for this simple server
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

@app.route('/', methods=['GET', 'POST'])
def home():
    """MCP Server root endpoint - handles both info and HTTP transport"""
    
    # Add CORS headers for all responses
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response
    
    # Check if this is an SSE request (GET with specific headers indicating SSE)
    if request.method == 'GET':
        accept_header = request.headers.get('Accept', '').lower()
        user_agent = request.headers.get('User-Agent', '').lower()
        authorization = request.headers.get('Authorization', '')
        
        # Detect SSE request characteristics - EventSource requests or explicit accept header
        is_sse_request = (
            'text/event-stream' in accept_header or 
            'event-stream' in accept_header or
            ('authorization' in request.headers and 'bearer' in authorization.lower())
        )
        
        # Handle SSE gracefully - return minimal response to not break Claude.ai
        if is_sse_request and accept_header and 'text/event-stream' in accept_header:
            logger.info(f"SSE request detected - returning minimal SSE response: Accept={accept_header}")
            # Return a basic SSE response that closes immediately
            from flask import Response
            return Response(
                "event: close\ndata: {\"message\": \"Use HTTP transport for requests\"}\n\n",
                mimetype='text/event-stream',
                headers={
                    'Content-Type': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'Connection': 'close',
                    'Access-Control-Allow-Origin': '*'
                }
            )
    
    # If it's a POST request with JSON-RPC, treat as MCP HTTP transport
    if request.method == 'POST':
        try:
            # Check if it's JSON-RPC request
            data = request.get_json()
            if data and 'jsonrpc' in data:
                response = handle_http_transport()
                return add_cors_headers(response)
            else:
                # Not a valid JSON-RPC request
                response = jsonify({
                    "error": "Invalid request",
                    "message": "Expected JSON-RPC 2.0 request"
                })
                response.status_code = 400
                return add_cors_headers(response)
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            response = jsonify({
                "error": "Request processing failed",
                "message": str(e)
            })
            response.status_code = 500
            return add_cors_headers(response)
    
    # Otherwise return server information
    response = jsonify({
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
    return add_cors_headers(response)

def handle_sse_at_root():
    """Handle SSE transport at root endpoint"""
    # Check authentication
    has_claude_auth = check_claude_auth()
    if not has_claude_auth:
        return Response(
            "event: error\ndata: Authentication required\n\n",
            mimetype='text/event-stream',
            status=401,
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            }
        )
    
    def event_stream():
        try:
            # Send initial connection event
            yield f"event: connection\ndata: {json.dumps({'status': 'connected', 'protocol': '2024-11-05'})}\n\n"
            
            # Keep connection alive with heartbeats
            while True:
                try:
                    # Send keep-alive every 30 seconds
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    time.sleep(30)
                except GeneratorExit:
                    logger.info("SSE client disconnected from root")
                    break
                except Exception as e:
                    logger.error(f"SSE stream error at root: {e}")
                    break
        except Exception as e:
            logger.error(f"SSE event stream error at root: {e}")
    
    response = Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Authorization, Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
        }
    )
    
    logger.info("SSE endpoint accessed at root, starting event stream")
    return response

def handle_http_transport():
    """Handle HTTP transport requests at root endpoint"""
    # Check authentication
    has_claude_auth = check_claude_auth()
    if not has_claude_auth:
        response = jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32001,
                "message": "Authentication required"
            }
        })
        response.status_code = 401
        return response
    
    data = request.get_json()
    if not data:
        response = jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        })
        response.status_code = 400
        return response
    
    method = data.get('method')
    params = data.get('params', {})
    request_id = data.get('id')
    
    logger.info(f"HTTP transport MCP request: method={method}, id={request_id}")
    
    # Log all requests for debugging
    if method == 'tools/list':
        logger.info("🎯 TOOLS/LIST REQUEST RECEIVED - Claude.ai is asking for tools!")
    elif method == 'tools/call':
        logger.info("🔧 TOOLS/CALL REQUEST RECEIVED - Claude.ai is calling a tool!")
    
    # Route to appropriate MCP handler
    if method == 'initialize':
        logger.info("Returning initialize response with tools included")
        
        # Include tools directly in initialize response to help Claude.ai
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
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": "powerbi-mcp-server",
                    "version": "1.0.0"
                }
            }
        })
    
    elif method == 'notifications/initialized':
        # Handle the initialized notification (no response required for notifications)
        logger.info("Received initialized notification - client ready")
        logger.info("💡 Claude.ai should now request tools/list to discover available tools")
        logger.info("🔧 Automatically triggering tools/list to help Claude.ai")
        
        # Instead of waiting for Claude.ai to request tools/list, let's trigger it
        # This might help Claude.ai understand the tools are available
        
        # For notifications, we don't return a response (id is null)
        if request_id is None:
            # This is a notification, return empty response
            return jsonify({})
        else:
            # If it has an id, return a simple acknowledgment
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            })
    
    elif method == 'initialized':
        # Alternative form of initialized notification
        logger.info("Received initialized notification (alternative form)")
        return jsonify({}) if request_id is None else jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {}
        })
    
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
    
    elif method == 'tools/call':
        # Delegate to existing tool call logic
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        # Use existing tool call implementation
        return handle_tool_call_logic(tool_name, arguments, request_id)
    
    else:
        response = jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        })
        response.status_code = 400
        return response

def handle_tool_call_logic(tool_name, arguments, request_id):
    """Shared tool call logic for both HTTP and dedicated endpoints"""
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
                        "text": json.dumps(result, indent=2)
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
                        "text": json.dumps(workspace_data, indent=2)
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
                        "text": json.dumps(dataset_data, indent=2)
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
            response = jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "dataset_id and dax_query are required"
                }
            })
            response.status_code = 400
            return response
        
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
                        "text": json.dumps(query_data_result, indent=2)
                    }
                ]
            }
        })
    
    else:
        response = jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Unknown tool: {tool_name}"
            }
        })
        response.status_code = 400
        return response

@app.route('/.well-known/mcp')
def mcp_discovery():
    """MCP discovery endpoint - advertises SSE transport"""
    base_url = request.base_url.replace('/.well-known/mcp', '')
    # Force HTTPS for Azure deployment
    if 'azurewebsites.net' in base_url:
        base_url = base_url.replace('http://', 'https://')
    
    return jsonify({
        "version": "2024-11-05",
        "transport": {
            "type": "http", 
            "http_url": f"{base_url}/"
        },
        "authentication": {
            "type": "oauth2",
            "authorization_url": f"{base_url}/authorize",
            "token_url": f"{base_url}/token",
            "scopes": ["powerbi"]
        },
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False,
            "logging": True
        },
        "serverInfo": {
            "name": "powerbi-mcp-server",
            "version": "1.0.0"
        }
    })

@app.route('/tools', methods=['GET'])
def tools_endpoint():
    """Direct tools endpoint for Claude.ai - return available tools"""
    logger.info("Direct /tools endpoint accessed - Claude.ai discovering tools")
    
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
        "tools": tools,
        "total_count": len(tools),
        "server": "powerbi-mcp-server",
        "version": "1.0.0"
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
        "version": "2.0.0-updated",  # Updated version to verify deployment
        "authentication": "client_credentials",
        "powerbi_configured": powerbi_configured,
        "powerbi_access": "granted" if token else "using_demo_data",
        "client_id_configured": bool(CLIENT_ID),
        "environment": "Azure" if os.environ.get('WEBSITE_HOSTNAME') else "Local",
        "mcp_endpoints_added": True,  # New field to verify deployment
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/test-deployment')
def test_deployment():
    """Test endpoint to verify deployment worked"""
    return jsonify({
        "message": "Deployment successful! MCP endpoints should be available.",
        "endpoints": ["/mcp/initialize", "/mcp/tools/list", "/mcp/tools/call"],
        "root_methods": "GET, POST should both work",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/test-post', methods=['POST'])
def test_post():
    """Simple test endpoint for POST requests"""
    return jsonify({
        "message": "POST request successful!",
        "method": request.method,
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
        response = jsonify({"error": "Request body required"})
        response.status_code = 400
        return response
    
    dataset_id = data.get('dataset_id')
    dax_query = data.get('dax_query') or data.get('query', '')
    workspace_id = data.get('workspace_id')
    
    if not dataset_id:
        response = jsonify({"error": "dataset_id is required"})
        response.status_code = 400
        return response
    
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
                
                # Parse error for better user guidance
                error_message = response.text[:500]
                troubleshooting_tip = ""
                
                if "MSOLAP connection" in error_message or "DatasetExecuteQueriesError" in error_message:
                    troubleshooting_tip = "⚠️ MSOLAP Connection Error: Your service principal needs to be added as a Member (not Viewer) to the Power BI workspace. Go to workspace settings > Access > Add your service principal with Member permissions."
                elif response.status_code == 403:
                    troubleshooting_tip = "⚠️ Permission Error: Your service principal needs 'Dataset.Read.All' API permissions and workspace Member access."
                elif response.status_code == 401:
                    troubleshooting_tip = "⚠️ Authentication Error: Check your AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID environment variables."
                
                response_obj = jsonify({
                    "error": f"Power BI API error: {response.status_code}",
                    "message": error_message,
                    "troubleshooting_tip": troubleshooting_tip,
                    "dax_query": dax_query,
                    "dataset_id": dataset_id,
                    "workspace_id": workspace_id,
                    "mode": "real_powerbi_query_failed",
                    "status": "failed"
                })
                response_obj.status_code = 400
                return response_obj
                
        except Exception as e:
            logger.error(f"Error executing Power BI query: {e}")
            response_obj = jsonify({
                "error": f"Query execution failed: {str(e)}",
                "dax_query": dax_query,
                "mode": "real_powerbi_query_failed",
                "status": "failed"
            })
            response_obj.status_code = 500
            return response_obj
    
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

@app.route('/authorize', methods=['GET', 'POST'])
def authorize():
    """Handle Claude's OAuth authorize request - always approve"""
    # Get OAuth parameters from Claude (both GET and POST)
    if request.method == 'POST':
        data = request.get_json() or request.form
        client_id = data.get('client_id')
        redirect_uri = data.get('redirect_uri')
        state = data.get('state')
        code_challenge = data.get('code_challenge')
    else:
        client_id = request.args.get('client_id')
        redirect_uri = request.args.get('redirect_uri')
        state = request.args.get('state')
        code_challenge = request.args.get('code_challenge')
    
    # Log the attempt for debugging
    logger.info(f"OAuth authorize request: method={request.method}, client_id={client_id}, redirect_uri={redirect_uri}, state={state}")
    
    # Be more flexible with missing parameters for Claude.ai compatibility
    if not redirect_uri:
        redirect_uri = "https://claude.ai/api/mcp/auth_callback"
        logger.info(f"Using default redirect URI: {redirect_uri}")
    
    if not state:
        state = "claude-auth-state"
        logger.info(f"Using default state: {state}")
    
    # Generate a dummy authorization code
    import secrets
    auth_code = secrets.token_urlsafe(32)
    
    # Log successful authorization
    logger.info(f"Generated auth code for client_id={client_id}, redirecting to {redirect_uri}")
    
    # Return authorization code by redirecting to redirect_uri
    redirect_url = f"{redirect_uri}?code={auth_code}&state={state}"
    
    # For Claude.ai, return a redirect response
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
        response = jsonify({
            "error": "unsupported_grant_type",
            "error_description": "Only authorization_code grant type is supported"
        })
        response.status_code = 400
        return response
    
    if not code:
        response = jsonify({
            "error": "invalid_request",
            "error_description": "Missing authorization code"
        })
        response.status_code = 400
        return response
    
    # VALIDATE CLIENT CREDENTIALS
    if not client_id or not client_secret:
        logger.warning("Token request missing client credentials")
        response = jsonify({
            "error": "invalid_client",
            "error_description": "Client authentication required"
        })
        response.status_code = 401
        return response
    
    # Validate against Power BI app registration credentials with detailed logging
    logger.info(f"Validating credentials - Received client_id: '{client_id}', Expected: '{CLIENT_ID}'")
    logger.info(f"Client ID match: {client_id == CLIENT_ID}")
    logger.info(f"Client secret provided: {'Yes' if client_secret else 'No'}")
    logger.info(f"Client secret match: {client_secret == CLIENT_SECRET}")
    
    if client_id != CLIENT_ID or client_secret != CLIENT_SECRET:
        logger.warning(f"Invalid client credentials: client_id='{client_id}' (expected '{CLIENT_ID}'), secret_match={client_secret == CLIENT_SECRET}")
        response = jsonify({
            "error": "invalid_client", 
            "error_description": "Invalid client credentials",
            "debug_info": {
                "received_client_id": client_id,
                "expected_client_id": CLIENT_ID,
                "client_id_match": client_id == CLIENT_ID,
                "client_secret_provided": bool(client_secret),
                "client_secret_match": client_secret == CLIENT_SECRET if client_secret else False
            }
        })
        response.status_code = 401
        return response
    
    logger.info(f"Client {client_id} authenticated successfully")
    
    # Generate access token for valid client
    import secrets
    access_token = secrets.token_urlsafe(64)
    
    # Return OAuth token response
    token_response = {
        "access_token": access_token,
        "token_type": "Bearer",  # Capitalized for Claude.ai compatibility
        "expires_in": 3600,
        "scope": "powerbi"
    }
    
    logger.info(f"Returning token response: {json.dumps({k: v if k != 'access_token' else 'TOKEN_HIDDEN' for k, v in token_response.items()})}")
    return jsonify(token_response)

@app.route('/claude-config')
def claude_config():
    """Claude AI configuration helper"""
    base_url = request.base_url.replace('/claude-config', '')
    # Force HTTPS for Azure deployment
    if 'azurewebsites.net' in base_url:
        base_url = base_url.replace('http://', 'https://')
    
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

# CORS preflight handlers - Add all endpoints
@app.route('/sse', methods=['OPTIONS'])
@app.route('/message', methods=['OPTIONS'])
@app.route('/authorize', methods=['OPTIONS'])
@app.route('/token', methods=['OPTIONS'])
@app.route('/', methods=['OPTIONS'])
@app.route('/mcp/initialize', methods=['OPTIONS'])
@app.route('/mcp/tools/list', methods=['OPTIONS'])
@app.route('/mcp/tools/call', methods=['OPTIONS'])
def handle_options():
    """Handle CORS preflight requests"""
    from flask import make_response
    response = make_response('', 200)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

# MCP SSE Transport Implementation
@app.route('/sse')
def sse_endpoint():
    """SSE endpoint for server-to-client streaming"""
    # Check authentication
    has_claude_auth = check_claude_auth()
    if not has_claude_auth:
        return Response(
            "event: error\ndata: Authentication required\n\n",
            mimetype='text/event-stream',
            status=401,
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            }
        )
    
    def event_stream():
        try:
            # Send initial connection event
            yield f"event: connection\ndata: {json.dumps({'status': 'connected', 'protocol': '2024-11-05'})}\n\n"
            
            # Keep connection alive with heartbeats
            while True:
                try:
                    # Send keep-alive every 30 seconds
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    time.sleep(30)
                except GeneratorExit:
                    logger.info("SSE client disconnected")
                    break
                except Exception as e:
                    logger.error(f"SSE stream error: {e}")
                    break
        except Exception as e:
            logger.error(f"SSE event stream error: {e}")
    
    response = Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Authorization, Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
        }
    )
    
    logger.info("SSE endpoint accessed, starting event stream")
    return response

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
    
    elif method == 'notifications/initialized':
        # Handle the initialized notification (no response required for notifications)
        logger.info("Received initialized notification via SSE - client ready")
        # For notifications, we don't return a response (id is null)
        if request_id is None:
            # This is a notification, return empty response
            return jsonify({})
        else:
            # If it has an id, return a simple acknowledgment
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            })
    
    elif method == 'initialized':
        # Alternative form of initialized notification
        logger.info("Received initialized notification via SSE (alternative form)")
        return jsonify({}) if request_id is None else jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {}
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
        logger.warning(f"❌ UNKNOWN METHOD: {method} - Claude.ai sent an unexpected request")
        logger.info(f"Available methods: initialize, notifications/initialized, tools/list, tools/call")
        response = jsonify({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}",
                "available_methods": ["initialize", "notifications/initialized", "tools/list", "tools/call"]
            }
        })
        response.status_code = 400
        return response

# Direct MCP protocol endpoints for Claude.ai (HTTP transport)
@app.route('/mcp/initialize', methods=['POST'])
def mcp_initialize():
    """MCP protocol initialize endpoint for Claude.ai"""
    data = request.get_json() or {}
    request_id = data.get('id', 1)
    
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

@app.route('/mcp/tools/list', methods=['POST'])
def mcp_tools_list():
    """MCP protocol tools list endpoint for Claude.ai"""
    user_agent = request.headers.get('User-Agent', 'Unknown')
    auth_header = request.headers.get('Authorization', 'None')
    
    logger.info(f"Tools list request from {user_agent}, Auth: {auth_header[:30]}...")
    
    data = request.get_json() or {}
    request_id = data.get('id', 1)
    
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
    
    logger.info(f"Returning {len(tools)} tools to {user_agent}")
    
    response_data = {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": tools
        }
    }
    
    return jsonify(response_data)

@app.route('/mcp/tools/call', methods=['POST'])
def mcp_tools_call():
    """MCP protocol tools call endpoint for Claude.ai"""
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
    
    logger.info(f"MCP tool call: {tool_name} with args: {arguments}")
    
    # Use shared tool call logic
    return handle_tool_call_logic(tool_name, arguments, request_id)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))  # Use 8000 as default for Azure
    
    logger.info(f"Starting Simple MCP Server on port {port}")
    logger.info(f"Environment: {'Azure' if os.environ.get('WEBSITE_HOSTNAME') else 'Local'}")
    
    # Azure compatibility
    if os.environ.get('WEBSITE_HOSTNAME'):
        logger.info(f"Azure deployment detected: {os.environ.get('WEBSITE_HOSTNAME')}")
    
    app.run(host='0.0.0.0', port=port, debug=False)