"""
Model schema discovery and caching system
Identifies actual table and column names in Power BI model
"""

import json
import base64
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

from .settings import settings
from ..utils.logging import mcp_logger
from ..powerbi.client import get_powerbi_client


@dataclass
class TableSchema:
    """Represents discovered table schema"""
    name: str
    columns: List[str]
    relationships: List[str] = None
    is_fact_table: bool = False
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.relationships is None:
            self.relationships = []


class ModelSchemaManager:
    """Manages model schema discovery and caching"""
    
    def __init__(self):
        self.cache_file = settings.script_dir / "model_schema_cache.json"
        self.cache_expiry_hours = 24
        self._cached_tables: Dict[str, TableSchema] = {}
        self._last_discovery: Optional[datetime] = None
        
        # Load cached data
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cached schema from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Check if cache is still valid
                cache_timestamp = datetime.fromisoformat(cache_data.get('timestamp', '1970-01-01'))
                if datetime.now() - cache_timestamp < timedelta(hours=self.cache_expiry_hours):
                    tables_data = cache_data.get('tables', {})
                    self._cached_tables = {
                        name: TableSchema(**data) 
                        for name, data in tables_data.items()
                    }
                    self._last_discovery = cache_timestamp
                    mcp_logger.info(f"Loaded {len(self._cached_tables)} cached table schemas")
                else:
                    mcp_logger.info("Model schema cache expired")
        except Exception as e:
            mcp_logger.warning(f"Could not load schema cache: {e}")
    
    def _save_cache(self) -> None:
        """Save schema to cache file"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'tables': {
                    name: {
                        'name': table.name,
                        'columns': table.columns,
                        'relationships': table.relationships,
                        'is_fact_table': table.is_fact_table,
                        'confidence': table.confidence
                    }
                    for name, table in self._cached_tables.items()
                }
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            mcp_logger.info(f"Saved {len(self._cached_tables)} table schemas to cache")
        except Exception as e:
            mcp_logger.error(f"Could not save schema cache: {e}")
    
    def _categorize_table(self, table_name: str, columns: List[str]) -> tuple[bool, float]:
        """Determine if table is a fact table and confidence level"""
        name_lower = table_name.lower()
        columns_lower = [col.lower() for col in columns]
        
        # Fact table indicators
        fact_indicators = ['journal', 'transaction', 'entry', 'line', 'fact']
        dimension_indicators = ['dim', '_date', '_period', 'account', 'contact', 'mapping']
        
        # Amount/value columns indicate fact table
        value_columns = [col for col in columns_lower if any(
            indicator in col for indicator in ['amount', 'value', 'quantity', 'balance']
        )]
        
        # ID columns indicate relationships
        id_columns = [col for col in columns_lower if col.endswith(' id') or col.endswith('id')]
        
        # Fact table scoring
        fact_score = 0
        if any(indicator in name_lower for indicator in fact_indicators):
            fact_score += 0.4
        if value_columns:
            fact_score += 0.3 + (len(value_columns) * 0.1)
        if len(id_columns) >= 3:  # Many relationships = likely fact table
            fact_score += 0.2
        
        # Dimension table penalties
        if any(indicator in name_lower for indicator in dimension_indicators):
            fact_score -= 0.3
        if len(columns) < 5:  # Small tables likely dimensions
            fact_score -= 0.1
        
        is_fact = fact_score > 0.5
        confidence = min(max(fact_score, 0.1), 1.0)
        
        return is_fact, confidence
    
    def discover_model_schema(self, 
                            workspace_name: str = None, 
                            dataset_name: str = None,
                            force_refresh: bool = False) -> Dict[str, TableSchema]:
        """Discover table and column schema from Power BI model"""
        workspace_name = workspace_name or settings.default_workspace_name
        dataset_name = dataset_name or settings.default_dataset_name
        
        # Cache disabled - always get fresh schema
        # Always refresh to ensure latest model structure from Power BI
        
        try:
            mcp_logger.info(f"Discovering model schema from {workspace_name}/{dataset_name}")
            client = get_powerbi_client()
            
            # Get workspace and dataset
            workspace = client.get_workspace_by_name(workspace_name)
            dataset = client.get_dataset_by_name(workspace['id'], dataset_name)
            
            discovered_tables = {}
            
            try:
                # Use the 4 DAX queries to understand model structure
                mcp_logger.info("Using new discovery method with 4 DAX queries")
                
                # Query 1: Get Tables with descriptions
                tables_query = """
                EVALUATE CALCULATETABLE( 
                    SELECTCOLUMNS(__def_Tables, [Name], [Description]), 
                    NOT(ISBLANK(__def_Tables[Description])) 
                )
                """
                
                # Query 2: Get Columns with table, name, and description
                columns_query = """
                EVALUATE CALCULATETABLE( 
                    SELECTCOLUMNS(__def_Columns, [Table], [Name], [Description]), 
                    NOT(ISBLANK(__def_Columns[Description])) 
                )
                """
                
                # Execute tables query
                tables_result = client.execute_dax_query(
                    workspace['id'], dataset['id'], tables_query
                )
                
                # Execute columns query
                columns_result = client.execute_dax_query(
                    workspace['id'], dataset['id'], columns_query
                )
                
                # Parse tables - Handle both result formats
                table_info = {}
                mcp_logger.info(f"Tables result format: {type(tables_result)}")
                mcp_logger.info(f"Tables result sample: {str(tables_result)[:500]}...")
                
                # Try custom DAX result format first (list with rows)
                if isinstance(tables_result, list) and len(tables_result) > 0:
                    first_result = tables_result[0]
                    if 'rows' in first_result:
                        rows = first_result['rows']
                        mcp_logger.info(f"Found {len(rows)} tables using custom DAX format")
                        for row in rows:
                            table_name = row.get('__def_Tables[Name]', '')
                            description = row.get('__def_Tables[Description]', '')
                            if table_name:
                                table_info[table_name] = description
                
                # Fallback to original result format
                elif 'results' in tables_result:
                    tables = tables_result['results'][0].get('tables', [])
                    if tables and 'rows' in tables[0]:
                        rows = tables[0]['rows']
                        mcp_logger.info(f"Found {len(rows)} tables using original format")
                        for row in rows:
                            table_name = row.get('__def_Tables[Name]', '')
                            description = row.get('__def_Tables[Description]', '')
                            if table_name:
                                table_info[table_name] = description
                
                # Parse columns and group by table - Handle both result formats  
                table_columns = {}
                mcp_logger.info(f"Columns result format: {type(columns_result)}")
                mcp_logger.info(f"Columns result sample: {str(columns_result)[:500]}...")
                
                # Try custom DAX result format first
                if isinstance(columns_result, list) and len(columns_result) > 0:
                    first_result = columns_result[0]
                    if 'rows' in first_result:
                        rows = first_result['rows']
                        mcp_logger.info(f"Found {len(rows)} columns using custom DAX format")
                        for row in rows:
                            table_name = row.get('__def_Columns[Table]', '')
                            column_name = row.get('__def_Columns[Name]', '')
                            column_desc = row.get('__def_Columns[Description]', '')
                            
                            if table_name and column_name:
                                if table_name not in table_columns:
                                    table_columns[table_name] = []
                                table_columns[table_name].append(column_name)
                
                # Fallback to original result format
                elif 'results' in columns_result:
                    tables = columns_result['results'][0].get('tables', [])
                    if tables and 'rows' in tables[0]:
                        rows = tables[0]['rows']
                        mcp_logger.info(f"Found {len(rows)} columns using original format")
                        for row in rows:
                            table_name = row.get('__def_Columns[Table]', '')
                            column_name = row.get('__def_Columns[Name]', '')
                            column_desc = row.get('__def_Columns[Description]', '')
                            
                            if table_name and column_name:
                                if table_name not in table_columns:
                                    table_columns[table_name] = []
                                table_columns[table_name].append(column_name)
                
                # Create TableSchema objects
                for table_name in table_info.keys():
                    columns = table_columns.get(table_name, [])
                    
                    # Categorize table as fact or dimension
                    is_fact, confidence = self._categorize_table(table_name, columns)
                    
                    discovered_tables[table_name] = TableSchema(
                        name=table_name,
                        columns=columns,
                        is_fact_table=is_fact,
                        confidence=confidence
                    )
                
                # Also add tables that have columns but no description (fallback)
                for table_name, columns in table_columns.items():
                    if table_name not in discovered_tables:
                        is_fact, confidence = self._categorize_table(table_name, columns)
                        discovered_tables[table_name] = TableSchema(
                            name=table_name,
                            columns=columns,
                            is_fact_table=is_fact,
                            confidence=confidence * 0.8  # Lower confidence for no description
                        )
                
                self._cached_tables = discovered_tables
                self._last_discovery = datetime.now()
                self._save_cache()
                
                mcp_logger.info(f"Discovered {len(discovered_tables)} table schemas using new DAX queries")
                return discovered_tables
                
            except Exception as e:
                mcp_logger.error(f"Failed to discover schema using DAX queries: {e}")
                return {}
                
        except Exception as e:
            mcp_logger.error(f"Failed to discover schema: {e}")
            return {}
    
    def get_table_by_name(self, table_name: str) -> Optional[TableSchema]:
        """Get table schema by name (case insensitive)"""
        for name, table in self._cached_tables.items():
            if name.lower() == table_name.lower():
                return table
        return None
    
    def get_fact_tables(self) -> List[TableSchema]:
        """Get tables identified as fact tables"""
        return [table for table in self._cached_tables.values() if table.is_fact_table]
    
    def get_dimension_tables(self) -> List[TableSchema]:
        """Get tables identified as dimension tables"""
        return [table for table in self._cached_tables.values() if not table.is_fact_table]
    
    def find_column_in_tables(self, column_name: str) -> List[str]:
        """Find which tables contain a specific column"""
        matching_tables = []
        for table_name, table in self._cached_tables.items():
            if any(col.lower() == column_name.lower() for col in table.columns):
                matching_tables.append(table_name)
        return matching_tables
    
    def get_corrected_table_name(self, assumed_name: str) -> Optional[str]:
        """Get correct table name for commonly assumed names"""
        assumed_lower = assumed_name.lower()
        
        # Common corrections
        corrections = {
            'date': '_Date',
            'period': '_Period', 
            'scenario': '_Scenario',
            'accounts': 'Accounts',
            'journals': 'Journals',
            'mapping': 'Mapping'
        }
        
        if assumed_lower in corrections:
            corrected = corrections[assumed_lower]
            if corrected in self._cached_tables:
                return corrected
        
        # Try exact match first
        for table_name in self._cached_tables:
            if table_name.lower() == assumed_lower:
                return table_name
        
        # Try partial match
        for table_name in self._cached_tables:
            if assumed_lower in table_name.lower() or table_name.lower() in assumed_lower:
                return table_name
        
        return None
    
    def get_column_suggestions(self, table_name: str, column_fragment: str) -> List[str]:
        """Get column name suggestions for a table"""
        table = self.get_table_by_name(table_name)
        if not table:
            return []
        
        fragment_lower = column_fragment.lower()
        suggestions = []
        
        for column in table.columns:
            if fragment_lower in column.lower():
                suggestions.append(column)
        
        return suggestions


# Global instance
model_schema_manager = ModelSchemaManager()