"""
Minimal Power BI MCP Server using FastMCP
Azure-compatible deployment following best practices
"""

import os
import logging
from datetime import datetime
from typing import Optional

from fastmcp import FastMCP
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Power BI Configuration
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET', '')
TENANT_ID = os.environ.get('AZURE_TENANT_ID', '')

# Create FastMCP server
mcp = FastMCP("Power BI MCP Server")

def get_powerbi_token() -> Optional[str]:
    """Get Power BI access token using client credentials"""
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        return None
    
    try:
        token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
        token_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': 'https://analysis.windows.net/powerbi/api/.default',
            'grant_type': 'client_credentials'
        }
        
        response = requests.post(token_url, data=token_data, timeout=30)
        if response.status_code == 200:
            return response.json().get('access_token')
        
    except Exception as e:
        logger.error(f"Token error: {e}")
    
    return None

@mcp.tool()
def powerbi_health() -> str:
    """Check Power BI server health and configuration"""
    token = get_powerbi_token()
    
    result = {
        "status": "healthy",
        "powerbi_configured": bool(token),
        "environment": "Azure" if os.environ.get('WEBSITE_HOSTNAME') else "Local",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    import json
    return json.dumps(result, indent=2)

@mcp.tool()
def powerbi_workspaces() -> str:
    """List Power BI workspaces"""
    token = get_powerbi_token()
    
    if token:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                "https://api.powerbi.com/v1.0/myorg/groups",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                workspaces = response.json().get("value", [])
                result = {
                    "workspaces": [
                        {
                            "id": ws["id"],
                            "name": ws["name"],
                            "type": ws.get("type", "Workspace")
                        } for ws in workspaces
                    ],
                    "count": len(workspaces),
                    "mode": "real_data"
                }
                import json
                return json.dumps(result, indent=2)
        except:
            pass
    
    # Demo data
    demo_workspaces = [
        {"id": "demo-ws-1", "name": "Finance Dashboard", "type": "Workspace"},
        {"id": "demo-ws-2", "name": "Sales Reports", "type": "Workspace"}
    ]
    
    result = {"workspaces": demo_workspaces, "count": 2, "mode": "demo_data"}
    import json
    return json.dumps(result, indent=2)

@mcp.tool()
def powerbi_datasets(workspace_id: Optional[str] = None) -> str:
    """Get Power BI datasets"""
    token = get_powerbi_token()
    
    if token:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets" if workspace_id else "https://api.powerbi.com/v1.0/myorg/datasets"
            
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                datasets = response.json().get("value", [])
                result = {
                    "datasets": [
                        {
                            "id": ds["id"],
                            "name": ds["name"],
                            "workspace_id": workspace_id
                        } for ds in datasets
                    ],
                    "count": len(datasets),
                    "mode": "real_data"
                }
                import json
                return json.dumps(result, indent=2)
        except:
            pass
    
    # Demo data
    demo_datasets = [
        {"id": "demo-ds-1", "name": "Financial KPIs", "workspace_id": workspace_id or "demo-ws-1"},
        {"id": "demo-ds-2", "name": "Sales Performance", "workspace_id": workspace_id or "demo-ws-2"}
    ]
    
    result = {"datasets": demo_datasets, "count": 2, "mode": "demo_data"}
    import json
    return json.dumps(result, indent=2)

@mcp.tool()
def powerbi_query(dataset_id: str, dax_query: str, workspace_id: Optional[str] = None) -> str:
    """Execute DAX query against Power BI dataset"""
    token = get_powerbi_token()
    
    if token:
        try:
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries" if workspace_id else f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/executeQueries"
            
            payload = {"queries": [{"query": dax_query}]}
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = {
                    "dataset_id": dataset_id,
                    "query": dax_query,
                    "results": response.json().get("results", []),
                    "mode": "real_data",
                    "status": "success"
                }
                import json
                return json.dumps(result, indent=2)
        except Exception as e:
            return f"Query failed: {str(e)}"
    
    # Demo data
    demo_results = {
        "demo-ds-1": [{"Metric": "Revenue", "Value": 1250000}],
        "demo-ds-2": [{"Product": "Product A", "Sales": 45000}]
    }
    
    results = demo_results.get(dataset_id, [{"Message": "Demo data"}])
    result = {
        "dataset_id": dataset_id,
        "query": dax_query,
        "results": results,
        "mode": "demo_data",
        "status": "success"
    }
    
    import json
    return json.dumps(result, indent=2)

# Create ASGI app for Azure deployment
app = mcp.http_app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting Power BI MCP Server on port {port}")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)