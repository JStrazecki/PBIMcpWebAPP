"""
Simplified Power BI MCP Server using FastMCP
Minimal authentication for easy Claude.ai connection
"""

import os
import sys
import logging
import json
from typing import Optional
from datetime import datetime

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
logger = logging.getLogger("pbi-fastmcp-simple")

# Power BI Client Credentials Configuration
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET', '')
TENANT_ID = os.environ.get('AZURE_TENANT_ID', '')

# Create FastMCP server
mcp = FastMCP(
    "Power BI MCP Server",
    version="1.0.0",
    description="Simplified Power BI integration for Claude.ai"
)

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

@mcp.tool()
async def powerbi_health(ctx: Context) -> str:
    """Check Power BI server health and configuration status"""
    token = get_powerbi_token()
    powerbi_configured = bool(token)
    
    result = {
        "status": "healthy",
        "service": "Power BI MCP Server (FastMCP Simplified)",
        "version": "1.0.0",
        "powerbi_configured": powerbi_configured,
        "powerbi_access": "granted" if token else "demo_mode",
        "environment": "Azure" if os.environ.get('WEBSITE_HOSTNAME') else "Local",
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

@mcp.tool()
async def powerbi_datasets(ctx: Context, workspace_id: Optional[str] = None) -> str:
    """Get Power BI datasets
    
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

@mcp.tool()
async def powerbi_query(
    ctx: Context,
    dataset_id: str,
    dax_query: str,
    workspace_id: Optional[str] = None
) -> str:
    """Execute a DAX query against a Power BI dataset
    
    Args:
        dataset_id: The Power BI dataset ID
        dax_query: The DAX query to execute
        workspace_id: Optional workspace ID
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
            {"Product": "Product B", "Sales": 32000},
            {"Product": "Product C", "Sales": 67000}
        ],
        "demo-ds-3": [
            {"Department": "Warehouse", "Orders": 1250},
            {"Department": "Shipping", "Orders": 1180}
        ]
    }
    
    results = demo_results.get(dataset_id, [{"Message": "No demo data"}])
    
    return json.dumps({
        "results": results,
        "mode": "demo_data"
    }, indent=2)

# Run the server
if __name__ == "__main__":
    import uvicorn
    
    # Get the ASGI app
    app = mcp.get_asgi_app(transport="http")
    
    # Run with uvicorn
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting FastMCP server on port {port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)