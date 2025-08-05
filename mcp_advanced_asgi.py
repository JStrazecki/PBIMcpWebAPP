"""
Advanced MCP Server for Power BI with Enhanced Features
Includes: Resources, Prompts, Advanced Tools, and Logging
"""

import os
import sys
import logging
import json
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

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
logger = logging.getLogger("pbi-mcp-advanced")

# Power BI Client Credentials Configuration
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET', '')
TENANT_ID = os.environ.get('AZURE_TENANT_ID', '')

# Power BI OAuth scopes
POWERBI_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]

# Cache for Power BI data
cache = {}
cache_expiry = {}
CACHE_DURATION = timedelta(minutes=5)

# Usage tracking
usage_stats = defaultdict(int)
tool_execution_times = defaultdict(list)


def get_powerbi_token() -> Optional[str]:
    """Get Power BI access token using client credentials flow"""
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        logger.warning("Power BI credentials not configured - using demo data")
        return None
    
    # Check cache
    if 'token' in cache and cache_expiry.get('token', datetime.min) > datetime.utcnow():
        return cache['token']
    
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
            token = token_info.get('access_token')
            
            # Cache the token
            cache['token'] = token
            cache_expiry['token'] = datetime.utcnow() + timedelta(minutes=50)
            
            logger.info("Successfully acquired Power BI access token")
            return token
        else:
            logger.error(f"Failed to get Power BI token: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting Power BI token: {e}")
        return None


# Tool implementations
async def powerbi_health() -> str:
    """Check Power BI server health and configuration status"""
    start_time = datetime.utcnow()
    usage_stats['powerbi_health'] += 1
    
    token = get_powerbi_token()
    powerbi_configured = bool(token)
    
    # Test Power BI API connectivity
    api_status = "unknown"
    if token:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                "https://api.powerbi.com/v1.0/myorg/availableFeatures",
                headers=headers,
                timeout=10
            )
            api_status = "connected" if response.status_code == 200 else f"error_{response.status_code}"
        except:
            api_status = "connection_failed"
    
    result = {
        "status": "healthy",
        "service": "Power BI MCP Server (Advanced)",
        "version": "2.0.0",
        "powerbi_configured": powerbi_configured,
        "powerbi_access": "granted" if token else "demo_mode",
        "api_status": api_status,
        "environment": "Azure" if os.environ.get('WEBSITE_HOSTNAME') else "Local",
        "cache_status": {
            "items": len(cache),
            "token_cached": 'token' in cache
        },
        "usage_stats": {
            "total_calls": sum(usage_stats.values()),
            "by_tool": dict(usage_stats)
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    execution_time = (datetime.utcnow() - start_time).total_seconds()
    tool_execution_times['powerbi_health'].append(execution_time)
    
    return json.dumps(result, indent=2)


async def powerbi_workspaces() -> str:
    """List Power BI workspaces accessible to the server"""
    start_time = datetime.utcnow()
    usage_stats['powerbi_workspaces'] += 1
    
    # Check cache
    cache_key = 'workspaces'
    if cache_key in cache and cache_expiry.get(cache_key, datetime.min) > datetime.utcnow():
        logger.info("Returning cached workspaces")
        return cache[cache_key]
    
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
                        "capacity_id": ws.get("capacityId"),
                        "is_on_dedicated_capacity": ws.get("isOnDedicatedCapacity", False)
                    })
                
                result = {
                    "workspaces": formatted_workspaces,
                    "total_count": len(formatted_workspaces),
                    "mode": "real_data",
                    "cached": False,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                result_json = json.dumps(result, indent=2)
                
                # Cache the result
                cache[cache_key] = result_json
                cache_expiry[cache_key] = datetime.utcnow() + CACHE_DURATION
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                tool_execution_times['powerbi_workspaces'].append(execution_time)
                
                return result_json
        except Exception as e:
            logger.error(f"Error fetching workspaces: {e}")
    
    # Demo data
    demo_workspaces = [
        {
            "id": "demo-ws-1", 
            "name": "Finance Dashboard", 
            "type": "Workspace", 
            "state": "Active",
            "capacity_id": None,
            "is_on_dedicated_capacity": False
        },
        {
            "id": "demo-ws-2", 
            "name": "Sales Reports", 
            "type": "Workspace", 
            "state": "Active",
            "capacity_id": "demo-cap-1",
            "is_on_dedicated_capacity": True
        },
        {
            "id": "demo-ws-3", 
            "name": "Operations Analytics", 
            "type": "Workspace", 
            "state": "Active",
            "capacity_id": None,
            "is_on_dedicated_capacity": False
        }
    ]
    
    result = {
        "workspaces": demo_workspaces,
        "total_count": len(demo_workspaces),
        "mode": "demo_data",
        "cached": False,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    execution_time = (datetime.utcnow() - start_time).total_seconds()
    tool_execution_times['powerbi_workspaces'].append(execution_time)
    
    return json.dumps(result, indent=2)


async def powerbi_datasets(workspace_id: Optional[str] = None) -> str:
    """Get Power BI datasets with enhanced metadata"""
    start_time = datetime.utcnow()
    usage_stats['powerbi_datasets'] += 1
    
    # Check cache
    cache_key = f'datasets_{workspace_id or "all"}'
    if cache_key in cache and cache_expiry.get(cache_key, datetime.min) > datetime.utcnow():
        logger.info(f"Returning cached datasets for {cache_key}")
        cached_data = json.loads(cache[cache_key])
        cached_data['cached'] = True
        return json.dumps(cached_data, indent=2)
    
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
                        "is_refreshable": ds.get("isRefreshable", False),
                        "is_effective_identity_required": ds.get("isEffectiveIdentityRequired", False),
                        "is_effective_identity_roles_required": ds.get("isEffectiveIdentityRolesRequired", False),
                        "target_storage_mode": ds.get("targetStorageMode"),
                        "created_date": ds.get("createdDate"),
                        "content_provider_type": ds.get("contentProviderType"),
                        "configured_by": ds.get("configuredBy")
                    })
                
                result = {
                    "workspace_id": workspace_id or "all_accessible",
                    "datasets": formatted_datasets,
                    "total_count": len(formatted_datasets),
                    "mode": "real_data",
                    "cached": False,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                result_json = json.dumps(result, indent=2)
                
                # Cache the result
                cache[cache_key] = result_json
                cache_expiry[cache_key] = datetime.utcnow() + CACHE_DURATION
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                tool_execution_times['powerbi_datasets'].append(execution_time)
                
                return result_json
        except Exception as e:
            logger.error(f"Error fetching datasets: {e}")
    
    # Demo data with enhanced metadata
    demo_datasets = [
        {
            "id": "demo-ds-1",
            "name": "Financial KPIs",
            "workspace_id": "demo-ws-1",
            "is_refreshable": True,
            "is_effective_identity_required": False,
            "target_storage_mode": "Import",
            "created_date": "2024-01-15T10:30:00Z",
            "content_provider_type": "PowerBI",
            "configured_by": "admin@contoso.com"
        },
        {
            "id": "demo-ds-2",
            "name": "Sales Performance",
            "workspace_id": "demo-ws-2",
            "is_refreshable": True,
            "is_effective_identity_required": True,
            "target_storage_mode": "DirectQuery",
            "created_date": "2024-02-20T14:45:00Z",
            "content_provider_type": "PowerBI",
            "configured_by": "analyst@contoso.com"
        },
        {
            "id": "demo-ds-3",
            "name": "Operations Metrics",
            "workspace_id": "demo-ws-3",
            "is_refreshable": False,
            "is_effective_identity_required": False,
            "target_storage_mode": "Import",
            "created_date": "2024-03-10T09:15:00Z",
            "content_provider_type": "File",
            "configured_by": "ops@contoso.com"
        }
    ]
    
    if workspace_id:
        demo_datasets = [ds for ds in demo_datasets if ds.get("workspace_id") == workspace_id]
    
    result = {
        "workspace_id": workspace_id or "all",
        "datasets": demo_datasets,
        "total_count": len(demo_datasets),
        "mode": "demo_data",
        "cached": False,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    execution_time = (datetime.utcnow() - start_time).total_seconds()
    tool_execution_times['powerbi_datasets'].append(execution_time)
    
    return json.dumps(result, indent=2)


async def powerbi_query(dataset_id: str, dax_query: str, workspace_id: Optional[str] = None) -> str:
    """Execute a DAX query against a Power BI dataset"""
    start_time = datetime.utcnow()
    usage_stats['powerbi_query'] += 1
    
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
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                tool_execution_times['powerbi_query'].append(execution_time)
                
                return json.dumps({
                    "dataset_id": dataset_id,
                    "workspace_id": workspace_id,
                    "query": dax_query,
                    "results": result_data.get("results", []),
                    "execution_time_seconds": execution_time,
                    "status": "success",
                    "mode": "real_data",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            else:
                error_detail = response.text[:500]
                return json.dumps({
                    "error": f"API error: {response.status_code}",
                    "message": error_detail,
                    "dataset_id": dataset_id,
                    "workspace_id": workspace_id,
                    "query": dax_query,
                    "mode": "real_data"
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return json.dumps({
                "error": str(e),
                "dataset_id": dataset_id,
                "query": dax_query
            }, indent=2)
    
    # Enhanced demo results
    demo_results = {
        "demo-ds-1": {
            "tables": [
                {
                    "rows": [
                        {"Month": "2024-01", "Revenue": 1250000, "Expenses": 850000, "Profit": 400000, "ProfitMargin": 0.32},
                        {"Month": "2024-02", "Revenue": 1350000, "Expenses": 900000, "Profit": 450000, "ProfitMargin": 0.33},
                        {"Month": "2024-03", "Revenue": 1450000, "Expenses": 950000, "Profit": 500000, "ProfitMargin": 0.34}
                    ]
                }
            ]
        },
        "demo-ds-2": {
            "tables": [
                {
                    "rows": [
                        {"Product": "Product A", "Region": "North", "Sales": 45000, "Units": 150, "AvgPrice": 300},
                        {"Product": "Product B", "Region": "South", "Sales": 32000, "Units": 95, "AvgPrice": 337},
                        {"Product": "Product C", "Region": "East", "Sales": 67000, "Units": 220, "AvgPrice": 305}
                    ]
                }
            ]
        },
        "demo-ds-3": {
            "tables": [
                {
                    "rows": [
                        {"Department": "Warehouse", "Orders": 1250, "OnTime": 1175, "Delayed": 75, "Efficiency": 0.94},
                        {"Department": "Shipping", "Orders": 1180, "OnTime": 1050, "Delayed": 130, "Efficiency": 0.89},
                        {"Department": "Returns", "Orders": 70, "OnTime": 64, "Delayed": 6, "Efficiency": 0.91}
                    ]
                }
            ]
        }
    }
    
    results = demo_results.get(dataset_id, {
        "tables": [{
            "rows": [{"Message": "No demo data available for this dataset"}]
        }]
    })
    
    execution_time = (datetime.utcnow() - start_time).total_seconds()
    tool_execution_times['powerbi_query'].append(execution_time)
    
    return json.dumps({
        "dataset_id": dataset_id,
        "workspace_id": workspace_id,
        "query": dax_query or "demo query",
        "results": [results],
        "execution_time_seconds": execution_time,
        "status": "success",
        "mode": "demo_data",
        "timestamp": datetime.utcnow().isoformat()
    }, indent=2)


async def clear_cache() -> str:
    """Clear all cached data"""
    usage_stats['clear_cache'] += 1
    
    items_cleared = len(cache)
    cache.clear()
    cache_expiry.clear()
    
    return json.dumps({
        "status": "success",
        "items_cleared": items_cleared,
        "message": "Cache cleared successfully",
        "timestamp": datetime.utcnow().isoformat()
    }, indent=2)


async def get_usage_stats() -> str:
    """Get detailed usage statistics"""
    usage_stats['get_usage_stats'] += 1
    
    # Calculate average execution times
    avg_times = {}
    for tool, times in tool_execution_times.items():
        if times:
            avg_times[tool] = {
                "avg_seconds": sum(times) / len(times),
                "min_seconds": min(times),
                "max_seconds": max(times),
                "total_calls": len(times)
            }
    
    return json.dumps({
        "total_calls": sum(usage_stats.values()),
        "calls_by_tool": dict(usage_stats),
        "execution_times": avg_times,
        "cache_info": {
            "cached_items": len(cache),
            "cache_keys": list(cache.keys())
        },
        "server_uptime": "Not tracked in this version",
        "timestamp": datetime.utcnow().isoformat()
    }, indent=2)


# Resources implementation
def get_resources() -> List[Dict[str, Any]]:
    """Get available resources"""
    return [
        {
            "uri": "powerbi://documentation/dax-reference",
            "name": "DAX Function Reference",
            "description": "Complete reference for Data Analysis Expressions (DAX) functions",
            "mimeType": "text/markdown",
            "content": """# DAX Function Reference

## Common Functions

### Aggregation Functions
- SUM(column) - Sum of all numbers in a column
- AVERAGE(column) - Average of all numbers in a column
- COUNT(column) - Count of non-blank values
- MAX(column) - Maximum value in a column
- MIN(column) - Minimum value in a column

### Filter Functions
- FILTER(table, condition) - Returns filtered table
- ALL(table/column) - Returns all rows ignoring filters
- CALCULATE(expression, filter1, filter2, ...) - Evaluates expression in modified filter context

### Time Intelligence
- TOTALYTD(expression, dates) - Year-to-date total
- SAMEPERIODLASTYEAR(dates) - Same period in previous year
- DATEADD(dates, number, interval) - Shift dates by interval

### Text Functions
- CONCATENATE(text1, text2) - Joins two text strings
- LEFT(text, num_chars) - Returns leftmost characters
- UPPER(text) - Converts text to uppercase
"""
        },
        {
            "uri": "powerbi://samples/queries",
            "name": "Sample DAX Queries",
            "description": "Common DAX query patterns for Power BI",
            "mimeType": "application/json",
            "content": json.dumps({
                "basic_queries": [
                    {
                        "name": "Total Sales",
                        "query": "EVALUATE SUMMARIZE(Sales, \"Total\", SUM(Sales[Amount]))"
                    },
                    {
                        "name": "Sales by Product",
                        "query": "EVALUATE SUMMARIZE(Sales, Product[ProductName], \"Total Sales\", SUM(Sales[Amount]))"
                    }
                ],
                "advanced_queries": [
                    {
                        "name": "YoY Growth",
                        "query": """EVALUATE
ADDCOLUMNS(
    VALUES(Calendar[Year]),
    \"Sales\", CALCULATE(SUM(Sales[Amount])),
    \"PrevYearSales\", CALCULATE(SUM(Sales[Amount]), SAMEPERIODLASTYEAR(Calendar[Date])),
    \"YoY Growth\", DIVIDE(
        CALCULATE(SUM(Sales[Amount])) - CALCULATE(SUM(Sales[Amount]), SAMEPERIODLASTYEAR(Calendar[Date])),
        CALCULATE(SUM(Sales[Amount]), SAMEPERIODLASTYEAR(Calendar[Date]))
    )
)"""
                    }
                ]
            }, indent=2)
        }
    ]


# Prompts implementation
def get_prompts() -> List[Dict[str, Any]]:
    """Get available prompts"""
    return [
        {
            "name": "analyze_dataset",
            "description": "Analyze a Power BI dataset and suggest insights",
            "arguments": [
                {
                    "name": "dataset_id",
                    "description": "The ID of the dataset to analyze",
                    "required": True
                },
                {
                    "name": "focus_area",
                    "description": "Specific area to focus on (e.g., 'sales trends', 'customer behavior')",
                    "required": False
                }
            ],
            "prompt": """I'll analyze the Power BI dataset {{dataset_id}}{{#focus_area}} with a focus on {{focus_area}}{{/focus_area}}.

First, let me explore the dataset structure and available measures. Then I'll run some analytical queries to identify key insights and patterns.

Based on the data, I'll provide:
1. Key metrics and KPIs
2. Notable trends and patterns
3. Potential areas for deeper investigation
4. Suggested visualizations for your reports"""
        },
        {
            "name": "optimize_dax",
            "description": "Optimize a DAX query for better performance",
            "arguments": [
                {
                    "name": "original_query",
                    "description": "The DAX query to optimize",
                    "required": True
                }
            ],
            "prompt": """I'll help optimize this DAX query for better performance:

```dax
{{original_query}}
```

Let me analyze the query structure and suggest optimizations based on:
1. Filter context optimization
2. Reducing row context transitions
3. Using variables for repeated calculations
4. Leveraging built-in optimization functions
5. Avoiding common performance pitfalls"""
        }
    ]


# ASGI application
async def app(scope, receive, send):
    """Advanced ASGI application with full MCP protocol support"""
    if scope['type'] == 'http':
        path = scope['path']
        
        # Handle root path
        if path == '/':
            if scope['method'] == 'GET':
                # Server info
                response_data = {
                    "name": "Power BI MCP Server (Advanced)",
                    "version": "2.0.0",
                    "protocol_version": "2024-11-05",
                    "capabilities": {
                        "tools": True,
                        "resources": True,
                        "prompts": True,
                        "logging": True
                    },
                    "features": [
                        "Caching for improved performance",
                        "Usage statistics and monitoring",
                        "Enhanced error handling",
                        "Resource documents",
                        "Prompt templates",
                        "Extended dataset metadata"
                    ]
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
                    
                    logger.info(f"MCP request: method={method}, params={params}")
                    
                    # Handle different MCP methods
                    if method == 'initialize':
                        response_data = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {
                                    "tools": {},
                                    "resources": {"subscribe": False},
                                    "prompts": {},
                                    "logging": {}
                                },
                                "serverInfo": {
                                    "name": "powerbi-mcp-server-advanced",
                                    "version": "2.0.0"
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
                                "description": "Check Power BI server health and detailed configuration status",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            },
                            {
                                "name": "powerbi_workspaces",
                                "description": "List Power BI workspaces with enhanced metadata",
                                "inputSchema": {
                                    "type": "object", 
                                    "properties": {},
                                    "required": []
                                }
                            },
                            {
                                "name": "powerbi_datasets",
                                "description": "Get Power BI datasets with detailed metadata",
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
                                "description": "Execute a DAX query with performance metrics",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "dataset_id": {
                                            "type": "string",
                                            "description": "The Power BI dataset ID"
                                        },
                                        "dax_query": {
                                            "type": "string",
                                            "description": "The DAX query to execute"
                                        },
                                        "workspace_id": {
                                            "type": "string",
                                            "description": "Optional workspace ID"
                                        }
                                    },
                                    "required": ["dataset_id", "dax_query"]
                                }
                            },
                            {
                                "name": "clear_cache",
                                "description": "Clear all cached Power BI data",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            },
                            {
                                "name": "get_usage_stats",
                                "description": "Get detailed server usage statistics",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
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
                    
                    elif method == 'resources/list':
                        resources = get_resources()
                        
                        response_data = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "resources": resources
                            }
                        }
                    
                    elif method == 'resources/read':
                        uri = params.get('uri')
                        resources = get_resources()
                        
                        resource = next((r for r in resources if r['uri'] == uri), None)
                        
                        if resource:
                            response_data = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": {
                                    "contents": [
                                        {
                                            "uri": resource['uri'],
                                            "mimeType": resource['mimeType'],
                                            "text": resource['content']
                                        }
                                    ]
                                }
                            }
                        else:
                            response_data = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {
                                    "code": -32602,
                                    "message": f"Resource not found: {uri}"
                                }
                            }
                    
                    elif method == 'prompts/list':
                        prompts = get_prompts()
                        
                        response_data = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "prompts": prompts
                            }
                        }
                    
                    elif method == 'prompts/get':
                        prompt_name = params.get('name')
                        prompts = get_prompts()
                        
                        prompt = next((p for p in prompts if p['name'] == prompt_name), None)
                        
                        if prompt:
                            response_data = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": prompt
                            }
                        else:
                            response_data = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {
                                    "code": -32602,
                                    "message": f"Prompt not found: {prompt_name}"
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
                        elif tool_name == 'clear_cache':
                            result_text = await clear_cache()
                        elif tool_name == 'get_usage_stats':
                            result_text = await get_usage_stats()
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
                    
                    elif method == 'logging/setLevel':
                        level = params.get('level', 'info').upper()
                        
                        # Set logging level
                        numeric_level = getattr(logging, level, logging.INFO)
                        logger.setLevel(numeric_level)
                        logging.getLogger().setLevel(numeric_level)
                        
                        response_data = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {}
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
                    logger.error(f"Error processing request: {e}", exc_info=True)
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    
                    if 'request_id' in locals():
                        error_response['id'] = request_id
                    
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
    logger.info(f"Starting Advanced MCP ASGI server on port {port}")
    logger.info("Features: Tools, Resources, Prompts, Caching, Statistics")
    uvicorn.run(app, host="0.0.0.0", port=port)