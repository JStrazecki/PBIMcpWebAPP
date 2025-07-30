"""
Simple MCP Server for Claude AI
No authentication required - direct connection
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("pbi-mcp-simple")

app = Flask(__name__)
CORS(app)

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
    return jsonify({
        "status": "healthy",
        "service": "Power BI MCP Server (Simple)",
        "authentication": "none",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/workspaces')
def workspaces():
    """List Power BI workspaces (demo data)"""
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
        "mode": "demo",
        "authentication": "none",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/datasets')
def datasets():
    """Get Power BI datasets (demo data)"""
    workspace_id = request.args.get('workspace_id')
    
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
    if workspace_id:
        filtered_datasets = [ds for ds in demo_datasets if ds["workspace_id"] == workspace_id]
    else:
        filtered_datasets = demo_datasets
    
    return jsonify({
        "workspace_id": workspace_id or "all",
        "datasets": filtered_datasets,
        "total_count": len(filtered_datasets),
        "mode": "demo",
        "authentication": "none",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/query', methods=['POST'])
def query():
    """Execute Power BI query (demo data)"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    dataset_id = data.get('dataset_id')
    query_description = data.get('query', 'No query provided')
    
    if not dataset_id:
        return jsonify({"error": "dataset_id is required"}), 400
    
    # Demo results based on dataset
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
        "query": query_description,
        "results": results,
        "mode": "demo",
        "authentication": "none",
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
    port = int(os.environ.get('PORT', 8001))
    
    logger.info(f"Starting Simple MCP Server on port {port}")
    logger.info(f"Server URL: http://localhost:{port}")
    logger.info(f"Claude config: http://localhost:{port}/claude-config")
    
    app.run(host='0.0.0.0', port=port, debug=False)