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
    from flask import Flask, jsonify, request, session, redirect, url_for
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
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
CORS(app)

# Initialize MCP server internally
mcp = FastMCP("powerbi-financial-server")

# OAuth 2.0 Configuration
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
TENANT_ID = os.environ.get('AZURE_TENANT_ID')
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'https://pbimcp.azurewebsites.net/auth/callback')

# Power BI OAuth scopes
SCOPES = [
    "https://analysis.windows.net/powerbi/api/Dataset.Read.All",
    "https://analysis.windows.net/powerbi/api/Report.Read.All", 
    "https://analysis.windows.net/powerbi/api/Workspace.Read.All",
    "https://analysis.windows.net/powerbi/api/Content.Create"
]

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
            "mcp_query": "/mcp/query"
        },
        "features": {
            "powerbi_integration": True,
            "mcp_bridge": True,
            "async_tools": True
        },
        "timestamp": datetime.utcnow().isoformat()
    })

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

def create_app():
    """Create Flask app for Azure deployment"""
    return app

# For Azure deployment
APP = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting MCP Bridge Server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)