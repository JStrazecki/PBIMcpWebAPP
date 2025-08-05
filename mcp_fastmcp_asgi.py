"""
Ultra-simple FastMCP server for Azure deployment
No OAuth, no complexity - just MCP protocol
"""

import os
import sys
import logging
import json
from typing import Optional
from datetime import datetime

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
logger = logging.getLogger("pbi-mcp-asgi")

# Power BI Client Credentials Configuration
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET', '')
TENANT_ID = os.environ.get('AZURE_TENANT_ID', '')

# Power BI OAuth scopes
POWERBI_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]


def get_powerbi_token() -> Optional[str]:
    """Get Power BI access token using client credentials flow"""
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        logger.warning("Power BI credentials not configured - using demo data")
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
            logger.error(f"Failed to get Power BI token: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting Power BI token: {e}")
        return None


# Tool implementations
async def powerbi_health() -> str:
    """Check Power BI server health and configuration status"""
    token = get_powerbi_token()
    powerbi_configured = bool(token)
    
    result = {
        "status": "healthy",
        "service": "Power BI MCP Server (ASGI)",
        "version": "1.0.0",
        "powerbi_configured": powerbi_configured,
        "powerbi_access": "granted" if token else "demo_mode",
        "environment": "Azure" if os.environ.get('WEBSITE_HOSTNAME') else "Local",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return json.dumps(result, indent=2)


async def powerbi_workspaces() -> str:
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
                        "state": ws.get("state", "Active")
                    })
                
                result = {
                    "workspaces": formatted_workspaces,
                    "total_count": len(formatted_workspaces),
                    "mode": "real_data"
                }
                
                return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error fetching workspaces: {e}")
    
    # Demo data
    demo_workspaces = [
        {"id": "demo-ws-1", "name": "Finance Dashboard", "type": "Workspace", "state": "Active"},
        {"id": "demo-ws-2", "name": "Sales Reports", "type": "Workspace", "state": "Active"},
        {"id": "demo-ws-3", "name": "Operations Analytics", "type": "Workspace", "state": "Active"}
    ]
    
    return json.dumps({
        "workspaces": demo_workspaces,
        "total_count": len(demo_workspaces),
        "mode": "demo_data"
    }, indent=2)


async def powerbi_datasets(workspace_id: Optional[str] = None) -> str:
    """Get Power BI datasets"""
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
                        "is_refreshable": ds.get("isRefreshable", False)
                    })
                
                result = {
                    "datasets": formatted_datasets,
                    "total_count": len(formatted_datasets),
                    "mode": "real_data"
                }
                
                return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error fetching datasets: {e}")
    
    # Demo data
    demo_datasets = [
        {"id": "demo-ds-1", "name": "Financial KPIs", "workspace_id": "demo-ws-1"},
        {"id": "demo-ds-2", "name": "Sales Performance", "workspace_id": "demo-ws-2"},
        {"id": "demo-ds-3", "name": "Operations Metrics", "workspace_id": "demo-ws-3"}
    ]
    
    if workspace_id:
        demo_datasets = [ds for ds in demo_datasets if ds.get("workspace_id") == workspace_id]
    
    return json.dumps({
        "datasets": demo_datasets,
        "total_count": len(demo_datasets),
        "mode": "demo_data"
    }, indent=2)


async def powerbi_query(dataset_id: str, dax_query: str, workspace_id: Optional[str] = None) -> str:
    """Execute a DAX query against a Power BI dataset"""
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
                "queries": [{"query": dax_query}],
                "serializerSettings": {"includeNulls": True}
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                result_data = response.json()
                return json.dumps({
                    "results": result_data.get("results", []),
                    "status": "success"
                }, indent=2)
            else:
                return json.dumps({
                    "error": f"API error: {response.status_code}",
                    "message": response.text[:200]
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return json.dumps({"error": str(e)}, indent=2)
    
    # Demo results
    demo_results = {
        "demo-ds-1": [
            {"Metric": "Total Revenue", "Value": 1250000},
            {"Metric": "Total Expenses", "Value": 850000},
            {"Metric": "Net Profit", "Value": 400000}
        ],
        "demo-ds-2": [
            {"Product": "Product A", "Sales": 45000},
            {"Product": "Product B", "Sales": 32000}
        ]
    }
    
    results = demo_results.get(dataset_id, [{"Message": "No demo data"}])
    
    return json.dumps({
        "results": results,
        "mode": "demo_data"
    }, indent=2)


# ASGI application
async def app(scope, receive, send):
    """ASGI application that handles MCP protocol directly"""
    if scope['type'] == 'http':
        path = scope['path']
        
        # Handle root path
        if path == '/':
            if scope['method'] == 'GET':
                # Server info
                response_data = {
                    "name": "Power BI MCP Server",
                    "version": "1.0.0",
                    "protocol_version": "2024-11-05",
                    "capabilities": {
                        "tools": True,
                        "resources": False,
                        "prompts": False
                    }
                }
                
                body = json.dumps(response_data).encode('utf-8')
                
                await send({
                    'type': 'http.response.start',
                    'status': 200,
                    'headers': [
                        [b'content-type', b'application/json'],
                        [b'access-control-allow-origin', b'*'],
                        [b'access-control-allow-headers', b'authorization, content-type'],
                        [b'access-control-allow-methods', b'GET, POST, OPTIONS'],
                    ]
                })
                
                await send({
                    'type': 'http.response.body',
                    'body': body
                })
                
            elif scope['method'] == 'POST':
                # Handle MCP requests
                body_parts = []
                while True:
                    message = await receive()
                    body_parts.append(message.get('body', b''))
                    if not message.get('more_body'):
                        break
                
                body = b''.join(body_parts)
                
                try:
                    data = json.loads(body)
                    method = data.get('method')
                    params = data.get('params', {})
                    request_id = data.get('id')
                    
                    logger.info(f"MCP request: method={method}")
                    
                    # Handle different MCP methods
                    if method == 'initialize':
                        response_data = {
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
                        }
                    
                    elif method == 'notifications/initialized':
                        # Notification - no response needed
                        response_data = {} if request_id is None else {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {}
                        }
                    
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
                                "description": "Get Power BI datasets",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "workspace_id": {
                                            "type": "string",
                                            "description": "Optional workspace ID"
                                        }
                                    },
                                    "required": []
                                }
                            },
                            {
                                "name": "powerbi_query",
                                "description": "Execute a DAX query",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "dataset_id": {"type": "string"},
                                        "dax_query": {"type": "string"},
                                        "workspace_id": {"type": "string"}
                                    },
                                    "required": ["dataset_id", "dax_query"]
                                }
                            }
                        ]
                        
                        response_data = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "tools": tools
                            }
                        }
                    
                    elif method == 'tools/call':
                        tool_name = params.get('name')
                        arguments = params.get('arguments', {})
                        
                        # Call the appropriate tool
                        if tool_name == 'powerbi_health':
                            result_text = await powerbi_health()
                        elif tool_name == 'powerbi_workspaces':
                            result_text = await powerbi_workspaces()
                        elif tool_name == 'powerbi_datasets':
                            result_text = await powerbi_datasets(arguments.get('workspace_id'))
                        elif tool_name == 'powerbi_query':
                            result_text = await powerbi_query(
                                arguments.get('dataset_id'),
                                arguments.get('dax_query'),
                                arguments.get('workspace_id')
                            )
                        else:
                            result_text = json.dumps({"error": f"Unknown tool: {tool_name}"})
                        
                        response_data = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": result_text
                                    }
                                ]
                            }
                        }
                    
                    else:
                        response_data = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {method}"
                            }
                        }
                    
                    # Send response
                    response_body = json.dumps(response_data).encode('utf-8')
                    
                    await send({
                        'type': 'http.response.start',
                        'status': 200,
                        'headers': [
                            [b'content-type', b'application/json'],
                            [b'access-control-allow-origin', b'*'],
                            [b'access-control-allow-headers', b'authorization, content-type'],
                            [b'access-control-allow-methods', b'GET, POST, OPTIONS'],
                        ]
                    })
                    
                    await send({
                        'type': 'http.response.body',
                        'body': response_body
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    
                    error_body = json.dumps(error_response).encode('utf-8')
                    
                    await send({
                        'type': 'http.response.start',
                        'status': 500,
                        'headers': [
                            [b'content-type', b'application/json'],
                            [b'access-control-allow-origin', b'*'],
                        ]
                    })
                    
                    await send({
                        'type': 'http.response.body',
                        'body': error_body
                    })
            
            elif scope['method'] == 'OPTIONS':
                # Handle CORS preflight
                await send({
                    'type': 'http.response.start',
                    'status': 200,
                    'headers': [
                        [b'access-control-allow-origin', b'*'],
                        [b'access-control-allow-headers', b'authorization, content-type'],
                        [b'access-control-allow-methods', b'GET, POST, OPTIONS'],
                    ]
                })
                
                await send({
                    'type': 'http.response.body',
                    'body': b''
                })
        
        else:
            # 404 for other paths
            await send({
                'type': 'http.response.start',
                'status': 404,
                'headers': [
                    [b'content-type', b'text/plain'],
                ]
            })
            
            await send({
                'type': 'http.response.body',
                'body': b'Not Found'
            })


# For gunicorn
application = app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting MCP ASGI server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)