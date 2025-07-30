"""
Simple MCP Server for Claude AI
No user authentication required - uses Azure client credentials for Power BI
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

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

# Power BI OAuth scopes for client credentials
POWERBI_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]

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
        "type": "remote_mcp_server",
        "authentication": "none",
        "capabilities": ["powerbi_workspaces", "powerbi_datasets", "powerbi_queries"],
        "claude_config": {
            "url": request.base_url.rstrip('/'),
            "authentication": "none"
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

@app.route('/claude-config')
def claude_config():
    """Claude AI configuration helper"""
    base_url = request.base_url.replace('/claude-config', '')
    
    return jsonify({
        "claude_setup": {
            "step_1": "Open Claude AI Settings > Connectors",
            "step_2": "Click 'Add Remote MCP Server'",
            "step_3": f"Enter URL: {base_url}",
            "step_4": "Set Authentication: None",
            "step_5": "Save and test connection"
        },
        "server_url": base_url,
        "authentication": "none",
        "test_command": "Ask Claude: 'Can you check the Power BI server health?'"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))  # Use 8000 as default for Azure
    
    logger.info(f"Starting Simple MCP Server on port {port}")
    logger.info(f"Environment: {'Azure' if os.environ.get('WEBSITE_HOSTNAME') else 'Local'}")
    
    # Azure compatibility
    if os.environ.get('WEBSITE_HOSTNAME'):
        logger.info(f"Azure deployment detected: {os.environ.get('WEBSITE_HOSTNAME')}")
    
    app.run(host='0.0.0.0', port=port, debug=False)