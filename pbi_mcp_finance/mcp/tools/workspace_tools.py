"""
MCP tools for Power BI workspace management
"""

from fastmcp import FastMCP
from typing import List, Dict, Any

from ...powerbi.client import get_powerbi_client
from ...config.settings import settings
from ...utils.logging import mcp_logger
from ...utils.exceptions import PowerBIError
from ...powerbi.permissions_handler import handle_powerbi_error


def register_workspace_tools(mcp: FastMCP):
    """Register workspace-related MCP tools"""
    
    @mcp.tool()
    def list_workspaces(filter_client: bool = True) -> str:
        """
        List Power BI workspaces with their available datasets.
        
        Args:
            filter_client: If True, only show client workspaces (default: True)
        
        Examples: 'show my workspaces', 'list all Power BI workspaces'
        """
        try:
            mcp_logger.info(f"Listing workspaces with datasets (filter_client={filter_client})")
            
            client = get_powerbi_client()
            workspaces = client.get_workspaces()
            
            if not workspaces:
                return "No workspaces found"
            
            # Show all workspaces or filter by client workspaces if requested
            filtered_workspaces = workspaces
            
            if filter_client:
                # If default workspace is configured, prioritize it but show others too
                default_workspace = settings.default_workspace_name
                if default_workspace:
                    # Move default workspace to the top of the list
                    default_ws = None
                    other_ws = []
                    for ws in workspaces:
                        if ws['name'] == default_workspace:
                            default_ws = ws
                        else:
                            other_ws.append(ws)
                    
                    if default_ws:
                        filtered_workspaces = [default_ws] + other_ws
            
            output = f"Power BI Workspaces ({len(filtered_workspaces)} found):\n\n"
            
            for workspace in filtered_workspaces:
                is_default = ""
                if workspace['name'] == settings.default_workspace_name:
                    is_default = " (configured default)"
                output += f"• {workspace['name']}{is_default}\n"
                output += f"  ID: {workspace['id']}\n"
                output += f"  Type: {workspace.get('type', 'Workspace')}\n"
                
                # List datasets in this workspace
                try:
                    datasets = client.get_datasets(workspace['id'])
                    if datasets:
                        output += f"  Datasets ({len(datasets)}):\n"
                        for dataset in datasets:
                            dataset_name = dataset.get('name', '<NO NAME>')
                            dataset_id = dataset.get('id', '')
                            output += f"    - {dataset_name}\n"
                            if dataset_id:
                                output += f"      ID: {dataset_id}\n"
                    else:
                        output += f"  Datasets: None available\n"
                except Exception as dataset_error:
                    # Check if this is a permissions error
                    error_str = str(dataset_error)
                    if "API is not accessible" in error_str or "403" in error_str:
                        output += f"  Datasets: Permission denied (Dataset.Read.All required)\n"
                    else:
                        output += f"  Datasets: Error retrieving ({error_str[:50]}...)\n"
                
                output += "\n"
            
            return output
                
        except PowerBIError as e:
            mcp_logger.error(f"Failed to list workspaces: {e}")
            return handle_powerbi_error(e, {"operation": "list_workspaces"})
        except Exception as e:
            mcp_logger.error(f"Unexpected error listing workspaces: {e}")
            return handle_powerbi_error(e, {"operation": "list_workspaces"})
    
    @mcp.tool()
    def list_datasets(workspace_name: str) -> str:
        """
        List all datasets/models available in a specific Power BI workspace.
        
        Args:
            workspace_name: Power BI workspace name (required)
        
        Examples: 'list datasets in Onetribe Demo', 'show available models'
        """
        try:
            mcp_logger.info(f"Listing datasets in workspace: {workspace_name}")
            
            client = get_powerbi_client()
            workspace = client.get_workspace_by_name(workspace_name)
            datasets = client.get_datasets(workspace['id'])
            
            if not datasets:
                return f"No datasets found in workspace '{workspace_name}'"
            
            output = f"Datasets in '{workspace_name}' ({len(datasets)} found):\n\n"
            
            for dataset in datasets:
                dataset_name = dataset.get('name', '<NO NAME>')
                dataset_id = dataset.get('id', '')
                config_mode = dataset.get('configuredBy', 'Unknown')
                target_storage_mode = dataset.get('targetStorageMode', 'Unknown')
                
                output += f"• {dataset_name}\n"
                output += f"  ID: {dataset_id}\n"
                output += f"  Mode: {target_storage_mode}\n"
                output += f"  Configuration: {config_mode}\n\n"
            
            output += f"💡 Use these dataset names with discovery tools:\n"
            output += f"   • discover_measures(workspace_name='{workspace_name}', dataset_name='<dataset_name>')\n"
            output += f"   • get_model_info(workspace_name='{workspace_name}', dataset_name='<dataset_name>')\n"
            
            return output
                
        except PowerBIError as e:
            mcp_logger.error(f"Failed to list datasets: {e}")
            return f"Error: {e}"
        except Exception as e:
            mcp_logger.error(f"Unexpected error listing datasets: {e}")
            return f"Error: Unexpected error occurred"
    
    @mcp.tool()
    def get_model_info(
        workspace_name: str,
        dataset_name: str
    ) -> str:
        """
        Get information about the dataset structure including tables, measures, and relationships.
        
        Args:
            workspace_name: Power BI workspace name (required)
            dataset_name: Dataset name (required)
        
        Examples: 'show me the data model', 'what tables are available?', 'list all measures'
        """
        try:
            mcp_logger.info(f"Getting model info for {workspace_name}/{dataset_name}")
            
            client = get_powerbi_client()
            
            # Get workspace and dataset
            workspace = client.get_workspace_by_name(workspace_name)
            dataset = client.get_dataset_by_name(workspace['id'], dataset_name)
            
            # Use the 4 DAX queries to get model information
            mcp_logger.info("Using new DAX queries for model information")
            
            # Query 1: Get Tables
            tables_query = """
            EVALUATE CALCULATETABLE( 
                SELECTCOLUMNS(__def_Tables, [Name], [Description]), 
                NOT(ISBLANK(__def_Tables[Description])) 
            )
            """
            
            # Query 2: Get Columns  
            columns_query = """
            EVALUATE CALCULATETABLE( 
                SELECTCOLUMNS(__def_Columns, [Table], [Name], [Description]), 
                NOT(ISBLANK(__def_Columns[Description])) 
            )
            """
            
            # Query 3: Get Measures
            measures_query = """
            EVALUATE CALCULATETABLE( 
                SELECTCOLUMNS(__def_Measures, [Name], [Description], [DisplayFolder]), 
                NOT(ISBLANK(__def_Measures[Description])) 
            )
            """
            
            # Query 4: Get Relationships
            relationships_query = """
            EVALUATE CALCULATETABLE(
                SELECTCOLUMNS(__def_Relationships, [Relationship]),
                __def_Relationships[IsActive] = TRUE() 
            )
            """
            
            tables = []
            measures = []
            relationships = []
            
            try:
                # Execute tables query
                tables_result = client.execute_dax_query(workspace['id'], dataset['id'], tables_query)
                if 'results' in tables_result:
                    result_tables = tables_result['results'][0].get('tables', [])
                    if result_tables and 'rows' in result_tables[0]:
                        rows = result_tables[0]['rows']
                        for row in rows:
                            table_name = row.get('__def_Tables[Name]', '')
                            if table_name:
                                tables.append(table_name)
                
                # Execute measures query
                measures_result = client.execute_dax_query(workspace['id'], dataset['id'], measures_query)
                if 'results' in measures_result:
                    result_tables = measures_result['results'][0].get('tables', [])
                    if result_tables and 'rows' in result_tables[0]:
                        rows = result_tables[0]['rows']
                        for row in rows:
                            measure_name = row.get('__def_Measures[Name]', '')
                            description = row.get('__def_Measures[Description]', '')
                            display_folder = row.get('__def_Measures[DisplayFolder]', '')
                            if measure_name:
                                measure_info = f"• {measure_name}"
                                if description:
                                    measure_info += f" - {description[:50]}..."
                                if display_folder:
                                    measure_info += f" [{display_folder}]"
                                measures.append(measure_info)
                
                # Execute relationships query  
                relationships_result = client.execute_dax_query(workspace['id'], dataset['id'], relationships_query)
                if 'results' in relationships_result:
                    result_tables = relationships_result['results'][0].get('tables', [])
                    if result_tables and 'rows' in result_tables[0]:
                        rows = result_tables[0]['rows']
                        for row in rows:
                            relationship = row.get('__def_Relationships[Relationship]', '')
                            if relationship:
                                relationships.append(relationship)
                        
            except Exception as e:
                mcp_logger.warning(f"Some DAX queries failed: {e}")
            
            # Format output
            output = f"Dataset Model Information\n{'='*50}\n\n"
            
            output += f"TABLES ({len(tables)})\n"
            for table in sorted(set(tables)):
                output += f"  • {table}\n"
            
            output += f"\nMEASURES ({len(measures)})\n"
            # Show only financial measures
            financial_keywords = ['Revenue', 'Profit', 'Cost', 'Cash', 'EBITDA', 'Margin', 'Asset', 'Debt', 'Sales', 'Income']
            relevant_measures = [m for m in measures if any(k.lower() in m.lower() for k in financial_keywords)]
            
            for measure in relevant_measures[:20]:  # Limit to top 20
                output += f"  {measure}\n"
            
            if len(relevant_measures) > 20:
                output += f"  ... and {len(relevant_measures) - 20} more financial measures\n"
            
            output += f"\nRELATIONSHIPS ({len(relationships)})\n"
            for rel in relationships[:10]:  # Show first 10 relationships
                output += f"  • {rel}\n"
            
            if len(relationships) > 10:
                output += f"  ... and {len(relationships) - 10} more relationships\n"
            
            return output
            
        except PowerBIError as e:
            mcp_logger.error(f"Failed to get model info: {e}")
            return f"Error: {e}"
        except Exception as e:
            mcp_logger.error(f"Unexpected error getting model info: {e}")
            return f"Error: Unexpected error occurred"