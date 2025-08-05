"""
MCP tools for custom DAX queries and data exploration
"""

import json
from fastmcp import FastMCP

from ...powerbi.client import get_powerbi_client
from ...config.settings import settings
from ...utils.logging import mcp_logger
from ...utils.exceptions import PowerBIError, DAXQueryError
from ...powerbi.permissions_handler import handle_powerbi_error


def register_query_tools(mcp: FastMCP):
    """Register custom query MCP tools"""
    
    @mcp.tool()
    def execute_custom_dax(
        query: str,
        workspace_name: str,
        dataset_name: str
    ) -> str:
        """
        Execute a custom DAX query for advanced analysis.
        
        Args:
            query: DAX query to execute
            workspace_name: Power BI workspace name (required)
            dataset_name: Dataset name (required)
        
        Examples: 
            'run DAX: EVALUATE VALUES(Accounts[Account Name])',
            'execute query to get all cost centers'
        """
        try:
            mcp_logger.info(f"Executing custom DAX query: {query[:100]}...")
            
            client = get_powerbi_client()
            
            # Get workspace and dataset
            workspace = client.get_workspace_by_name(workspace_name)
            dataset = client.get_dataset_by_name(workspace['id'], dataset_name)
            
            # Execute query
            result = client.execute_dax_query(workspace['id'], dataset['id'], query)
            
            # Return formatted JSON results
            results = result.get("results", [])
            if results and "tables" in results[0]:
                return json.dumps(results[0]["tables"], indent=2)
            else:
                return "No data returned"
                
        except (PowerBIError, DAXQueryError) as e:
            mcp_logger.error(f"Failed to execute custom DAX: {e}")
            context = {
                "operation": "execute_dax",
                "workspace_name": workspace_name,
                "dataset_name": dataset_name,
                "query_preview": query[:100] + "..." if len(query) > 100 else query
            }
            if 'workspace' in locals() and 'id' in workspace:
                context["workspace_id"] = workspace['id']
            if 'dataset' in locals() and 'id' in dataset:
                context["dataset_id"] = dataset['id']
            return handle_powerbi_error(e, context)
        except Exception as e:
            mcp_logger.error(f"Unexpected error executing DAX: {e}")
            return handle_powerbi_error(e, {
                "operation": "execute_dax",
                "workspace_name": workspace_name,
                "dataset_name": dataset_name
            })