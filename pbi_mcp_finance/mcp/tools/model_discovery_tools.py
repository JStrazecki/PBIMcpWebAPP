"""
Model discovery tools using proven custom DAX queries from logs
These replace the non-working discovery functions with working implementations
"""

import json
from datetime import datetime
from fastmcp import FastMCP

from ...powerbi.client import get_powerbi_client  
from ...utils.logging import mcp_logger


def register_model_discovery_tools(mcp: FastMCP):
    """Register working model discovery tools based on successful custom DAX queries"""
    
    @mcp.tool()
    def discover_model_tables(
        workspace_name: str,
        dataset_name: str
    ) -> str:
        """
        Discover all tables in the Power BI model using proven DAX query.
        
        Args:
            workspace_name: Power BI workspace name (required)
            dataset_name: Dataset name (required)
        """
        try:
            mcp_logger.info(f"Discovering tables: {workspace_name}/{dataset_name}")
            
            client = get_powerbi_client()
            workspace = client.get_workspace_by_name(workspace_name)
            dataset = client.get_dataset_by_name(workspace['id'], dataset_name)
            
            # Use EXACT working query from logs (line 64)
            tables_query = "EVALUATE CALCULATETABLE( SELECTCOLUMNS(__def_Tables, [Name], [Description]), NOT(ISBLANK(__def_Tables[Description])) )"
            
            result = client.execute_dax_query(workspace['id'], dataset['id'], tables_query)
            
            output = f"📊 MODEL TABLES DISCOVERY\n"
            output += f"Workspace: {workspace_name}\n"
            output += f"Dataset: {dataset_name}\n"
            output += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += "=" * 60 + "\n\n"
            
            # Parse result exactly like successful logs
            results = result.get("results", [])
            if results and len(results) > 0 and "tables" in results[0]:
                tables_data = results[0]["tables"]
                if tables_data and len(tables_data) > 0 and "rows" in tables_data[0]:
                    rows = tables_data[0]["rows"]
                    output += f"🎯 DISCOVERED {len(rows)} TABLES:\n\n"
                    
                    # Format exactly like successful response
                    for row in rows:
                        table_name = row.get('__def_Tables[Name]', '')
                        description = row.get('__def_Tables[Description]', '')
                        
                        # Classify table type based on description
                        if 'fact' in description.lower() or 'transaction' in description.lower():
                            emoji = "🎯"
                            table_type = "(Fact Table)"
                        elif 'dimension' in description.lower() or any(dim in table_name.lower() for dim in ['_date', 'accounts', 'contacts', 'mapping']):
                            emoji = "📋"
                            table_type = "(Dimension)"
                        else:
                            emoji = "📊"
                            table_type = ""
                        
                        output += f"  {emoji} {table_name} {table_type}\n"
                        if description:
                            output += f"    📝 {description}\n"
                        output += "\n"
                else:
                    output += "❌ No tables found in response structure\n"
            else:
                output += "❌ No tables discovered\n"
                output += "This indicates model access issues or parsing problems.\n"
            
            return output
            
        except Exception as e:
            error_msg = f"❌ Error discovering tables: {str(e)}"
            mcp_logger.error(error_msg)
            return error_msg
    
    @mcp.tool()
    def discover_model_columns(
        workspace_name: str,
        dataset_name: str
    ) -> str:
        """
        Discover all columns in the Power BI model using proven DAX query.
        
        Args:
            workspace_name: Power BI workspace name (required)
            dataset_name: Dataset name (required)
        """
        try:
            mcp_logger.info(f"Discovering columns: {workspace_name}/{dataset_name}")
            
            client = get_powerbi_client()
            workspace = client.get_workspace_by_name(workspace_name)
            dataset = client.get_dataset_by_name(workspace['id'], dataset_name)
            
            # Use EXACT working query from logs (line 101)
            columns_query = "EVALUATE CALCULATETABLE( SELECTCOLUMNS(__def_Columns, [Table], [Name], [Description]), NOT(ISBLANK(__def_Columns[Description])) )"
            
            result = client.execute_dax_query(workspace['id'], dataset['id'], columns_query)
            
            output = f"🔍 MODEL COLUMNS DISCOVERY\n"
            output += f"Workspace: {workspace_name}\n"
            output += f"Dataset: {dataset_name}\n"
            output += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += "=" * 60 + "\n\n"
            
            # Parse result exactly like successful logs
            results = result.get("results", [])
            if results and len(results) > 0 and "tables" in results[0]:
                tables_data = results[0]["tables"]
                if tables_data and len(tables_data) > 0 and "rows" in tables_data[0]:
                    rows = tables_data[0]["rows"]
                    output += f"🎯 DISCOVERED {len(rows)} COLUMNS:\n\n"
                    
                    # Group columns by table - matches successful format
                    tables_columns = {}
                    for row in rows:
                        table_name = row.get('__def_Columns[Table]', '')
                        column_name = row.get('__def_Columns[Name]', '')
                        description = row.get('__def_Columns[Description]', '')
                        
                        if table_name not in tables_columns:
                            tables_columns[table_name] = []
                        tables_columns[table_name].append((column_name, description))
                    
                    # Show columns exactly like successful response
                    for table_name, columns in tables_columns.items():
                        output += f"📋 {table_name}:\n"
                        for column_name, description in columns:
                            output += f"  • {column_name}\n"
                            if description:
                                output += f"    📝 {description}\n"
                        output += "\n"
                else:
                    output += "❌ No columns found in response structure\n"
            else:
                output += "❌ No columns discovered\n"
                output += "This indicates model access issues or parsing problems.\n"
            
            return output
            
        except Exception as e:
            error_msg = f"❌ Error discovering columns: {str(e)}"
            mcp_logger.error(error_msg)
            return error_msg
    
    @mcp.tool()
    def discover_model_measures(
        workspace_name: str,
        dataset_name: str
    ) -> str:
        """
        Discover all measures in the Power BI model using proven DAX query.
        
        Args:
            workspace_name: Power BI workspace name (required)
            dataset_name: Dataset name (required)
        """
        try:
            mcp_logger.info(f"Discovering measures: {workspace_name}/{dataset_name}")
            
            client = get_powerbi_client()
            workspace = client.get_workspace_by_name(workspace_name)
            dataset = client.get_dataset_by_name(workspace['id'], dataset_name)
            
            # Use EXACT working query from logs (line 140)
            measures_query = "EVALUATE CALCULATETABLE( SELECTCOLUMNS(__def_Measures, [Name], [Description], [DisplayFolder]), NOT(ISBLANK(__def_Measures[Description])) )"
            
            result = client.execute_dax_query(workspace['id'], dataset['id'], measures_query)
            
            output = f"📊 MODEL MEASURES DISCOVERY\n"
            output += f"Workspace: {workspace_name}\n"
            output += f"Dataset: {dataset_name}\n"
            output += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += "=" * 60 + "\n\n"
            
            # Parse result exactly like successful logs
            results = result.get("results", [])
            if results and len(results) > 0 and "tables" in results[0]:
                tables_data = results[0]["tables"]
                if tables_data and len(tables_data) > 0 and "rows" in tables_data[0]:
                    rows = tables_data[0]["rows"]
                    output += f"🎯 DISCOVERED {len(rows)} MEASURES:\n\n"
                    
                    # Group by display folder - exactly like successful logs show
                    folders = {}
                    for row in rows:
                        measure_name = row.get('__def_Measures[Name]', '')
                        description = row.get('__def_Measures[Description]', '')
                        display_folder = row.get('__def_Measures[DisplayFolder]', 'Other')
                        
                        if display_folder not in folders:
                            folders[display_folder] = []
                        folders[display_folder].append((measure_name, description))
                    
                    # Show by folder - matches successful response format
                    for folder_name, measures in folders.items():
                        emoji = "💰" if "Income" in folder_name else "📊"
                        output += f"{emoji} {folder_name}:\n"
                        for measure_name, description in measures:
                            output += f"  • {measure_name}\n"
                            if description:
                                output += f"    📝 {description}\n"
                        output += "\n"
                    
                    output += "⚠️ CRITICAL: ALWAYS use these existing measures for calculations!\n"
                    output += "⚠️ NEVER recreate measures that already exist!\n"
                else:
                    output += "❌ No measures found in response structure\n"
            else:
                output += "❌ No measures discovered\n"
                output += "Possible issues:\n"
                output += "• Model permissions restricted\n"
                output += "• Dataset refresh needed\n"
                output += "• Network connectivity problems\n"
            
            return output
            
        except Exception as e:
            error_msg = f"❌ Error discovering measures: {str(e)}"
            mcp_logger.error(error_msg)
            return error_msg
    
    @mcp.tool()
    def discover_model_relationships(
        workspace_name: str,
        dataset_name: str
    ) -> str:
        """
        Discover all active relationships in the Power BI model using proven DAX query.
        
        Args:
            workspace_name: Power BI workspace name (required)
            dataset_name: Dataset name (required)
        """
        try:
            mcp_logger.info(f"Discovering relationships: {workspace_name}/{dataset_name}")
            
            client = get_powerbi_client()
            workspace = client.get_workspace_by_name(workspace_name)
            dataset = client.get_dataset_by_name(workspace['id'], dataset_name)
            
            # Use EXACT working query from logs (line 164)
            relationships_query = "EVALUATE CALCULATETABLE( SELECTCOLUMNS(__def_Relationships, [Relationship]), __def_Relationships[IsActive] = TRUE() )"
            
            result = client.execute_dax_query(workspace['id'], dataset['id'], relationships_query)
            
            output = f"🔗 MODEL RELATIONSHIPS DISCOVERY\n"
            output += f"Workspace: {workspace_name}\n"
            output += f"Dataset: {dataset_name}\n"
            output += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += "=" * 60 + "\n\n"
            
            # Parse result exactly like successful logs
            results = result.get("results", [])
            if results and len(results) > 0 and "tables" in results[0]:
                tables_data = results[0]["tables"]
                if tables_data and len(tables_data) > 0 and "rows" in tables_data[0]:
                    rows = tables_data[0]["rows"]
                    output += f"🎯 DISCOVERED {len(rows)} ACTIVE RELATIONSHIPS:\n\n"
                    
                    # Format exactly like successful response
                    for i, row in enumerate(rows, 1):
                        relationship = row.get('__def_Relationships[Relationship]', '')
                        output += f"{i}. {relationship}\n"
                    
                    output += f"\n💡 RELATIONSHIP ANALYSIS:\n"
                    output += f"• These relationships define how tables connect\n"
                    output += f"• Active relationships are used in DAX calculations\n"
                    output += f"• Essential for understanding data model structure\n"
                    output += f"• Use these for writing proper DAX queries\n"
                    
                    # Analyze fact table connections - look for main fact table
                    fact_relationships = [row for row in rows if 'Journals' in row.get('__def_Relationships[Relationship]', '')]
                    if fact_relationships:
                        output += f"\n📊 FACT TABLE CONNECTIONS:\n"
                        for rel_row in fact_relationships:
                            relationship = rel_row.get('__def_Relationships[Relationship]', '')
                            output += f"  • {relationship}\n"
                        
                else:
                    output += "❌ No relationships found in response structure\n"
            else:
                output += "❌ No relationships discovered\n"
                output += "Possible issues:\n"
                output += "• Model permissions restricted\n"
                output += "• Dataset refresh needed\n"
                output += "• Network connectivity problems\n"
            
            return output
            
        except Exception as e:
            error_msg = f"❌ Error discovering relationships: {str(e)}"
            mcp_logger.error(error_msg)
            return error_msg
    
