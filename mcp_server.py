"""
Pure MCP Server for Claude.ai Enterprise Integration
Provides Power BI tools through Model Context Protocol
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

# Configure logging to stderr for MCP compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Important: MCP servers must log to stderr, not stdout
)
logger = logging.getLogger("pbi-mcp-server")

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import Resource, Tool
    import requests
    import msal
    import jwt
    logger.info("MCP and required libraries imported successfully")
except ImportError as e:
    logger.error(f"Failed to import required libraries: {e}")
    raise

# Initialize MCP server
mcp = FastMCP("powerbi-financial-server")

# OAuth 2.0 Configuration for Microsoft Authentication
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
TENANT_ID = os.environ.get('AZURE_TENANT_ID')

# Power BI OAuth scopes
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

async def get_client_credentials_token() -> Optional[str]:
    """Get application-level token using client credentials flow"""
    if not msal_app:
        logger.error("MSAL app not configured")
        return None
    
    try:
        # Use client credentials flow for application-level access
        result = msal_app.acquire_token_for_client(scopes=SCOPES)
        
        if "access_token" in result:
            logger.info("Successfully acquired Power BI token via client credentials")
            return result["access_token"]
        else:
            error_desc = result.get('error_description', 'Unknown error')
            logger.error(f"Failed to acquire Power BI token: {error_desc}")
            return None
            
    except Exception as e:
        logger.error(f"Error in client credentials flow: {e}")
        return None

@mcp.tool()
async def get_powerbi_status() -> Dict[str, Any]:
    """Get Power BI authentication and server status"""
    token = await get_client_credentials_token()
    
    return {
        "server_status": "running",
        "powerbi_access": "granted" if token else "denied",
        "authentication": "client_credentials",
        "service": "Power BI MCP Finance Server",
        "version": "3.0.0-mcp",
        "timestamp": datetime.utcnow().isoformat()
    }

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check for the MCP server"""
    token = await get_client_credentials_token()
    
    return {
        "status": "healthy",
        "service": "Power BI MCP Finance Server",
        "version": "3.0.0-mcp",
        "protocol": "model_context_protocol",
        "environment": "azure" if os.environ.get('WEBSITE_HOSTNAME') else "local",
        "authentication": {
            "type": "client_credentials",
            "configured": bool(msal_app),
            "powerbi_access": bool(token)
        },
        "features": {
            "powerbi_integration": True,
            "mcp_tools": True,
            "async_operations": True
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
            
    except requests.exceptions.Timeout:
        return {
            "error": "Power BI API timeout",
            "message": "Request timed out after 30 seconds"
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
            
    except requests.exceptions.Timeout:
        return {
            "error": "Query execution timeout", 
            "message": "Query timed out after 120 seconds",
            "query": dax_query
        }
    except Exception as e:
        return {
            "error": f"Failed to execute query: {str(e)}",
            "query": dax_query
        }

def main():
    """Main entry point for MCP server"""
    logger.info("Starting Power BI MCP Server")
    
    # Check OAuth configuration
    oauth_configured = bool(msal_app)
    logger.info(f"OAuth authentication configured: {oauth_configured}")
    
    if not oauth_configured:
        logger.warning("OAuth not configured - set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID")
    
    logger.info("Available MCP tools: get_powerbi_status, health_check, list_powerbi_workspaces, get_powerbi_datasets, execute_powerbi_query")
    
    # Run the MCP server
    mcp.run()

if __name__ == "__main__":
    main()