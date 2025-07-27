"""
Dynamic measure discovery and caching system
Bridges generic measure names with actual Power BI model measures
"""

import json
import os
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from .constants import FINANCIAL_MEASURES
from .settings import settings
from ..utils.logging import mcp_logger
from ..powerbi.client import get_powerbi_client


@dataclass
class DiscoveredMeasure:
    """Represents a discovered measure from Power BI model"""
    name: str
    formula: str = ""
    category: str = "unknown"
    confidence: float = 0.0
    aliases: List[str] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []


class DynamicMeasureManager:
    """Manages dynamic measure discovery and caching"""
    
    def __init__(self):
        self.cache_file = settings.script_dir / "measure_cache.json"
        self.mapping_file = settings.script_dir / "measure_mappings.json"
        self.cache_expiry_hours = 24  # Cache expires after 24 hours
        self._cached_measures: Dict[str, DiscoveredMeasure] = {}
        self._measure_mappings: Dict[str, str] = {}
        self._last_discovery: Optional[datetime] = None
        
        # Load cached data on initialization
        self._load_cache()
        self._load_mappings()
    
    def _load_cache(self) -> None:
        """Load cached measures from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Check if cache is still valid
                cache_timestamp = datetime.fromisoformat(cache_data.get('timestamp', '1970-01-01'))
                if datetime.now() - cache_timestamp < timedelta(hours=self.cache_expiry_hours):
                    measures_data = cache_data.get('measures', {})
                    self._cached_measures = {
                        name: DiscoveredMeasure(**data) 
                        for name, data in measures_data.items()
                    }
                    self._last_discovery = cache_timestamp
                    mcp_logger.info(f"Loaded {len(self._cached_measures)} cached measures")
                else:
                    mcp_logger.info("Measure cache expired, will refresh on next discovery")
        except Exception as e:
            mcp_logger.warning(f"Could not load measure cache: {e}")
    
    def _save_cache(self) -> None:
        """Save measures to cache file"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'measures': {
                    name: {
                        'name': measure.name,
                        'formula': measure.formula,
                        'category': measure.category,
                        'confidence': measure.confidence,
                        'aliases': measure.aliases
                    }
                    for name, measure in self._cached_measures.items()
                }
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            mcp_logger.info(f"Saved {len(self._cached_measures)} measures to cache")
        except Exception as e:
            mcp_logger.error(f"Could not save measure cache: {e}")
    
    def _load_mappings(self) -> None:
        """Load custom measure mappings"""
        try:
            if self.mapping_file.exists():
                with open(self.mapping_file, 'r') as f:
                    self._measure_mappings = json.load(f)
                mcp_logger.info(f"Loaded {len(self._measure_mappings)} custom measure mappings")
        except Exception as e:
            mcp_logger.warning(f"Could not load measure mappings: {e}")
    
    def _categorize_measure(self, measure_name: str, formula: str = "") -> Tuple[str, float, List[str]]:
        """Categorize a measure and assign confidence score"""
        name_lower = measure_name.lower()
        formula_lower = formula.lower()
        
        # Revenue detection
        revenue_keywords = ['revenue', 'sales', 'income', 'turnover', 'receipts']
        if any(keyword in name_lower for keyword in revenue_keywords):
            aliases = [kw for kw in revenue_keywords if kw in name_lower]
            return 'revenue', 0.9, aliases
        
        # Profit detection
        profit_keywords = ['profit', 'margin', 'earnings', 'ebitda', 'ebit']
        if any(keyword in name_lower for keyword in profit_keywords):
            if 'gross' in name_lower:
                return 'gross_profit', 0.85, ['gross profit', 'gp']
            elif 'ebitda' in name_lower:
                return 'ebitda', 0.9, ['ebitda', 'operating profit']
            elif 'net' in name_lower:
                return 'net_profit', 0.85, ['net profit', 'net income']
            return 'profit', 0.7, []
        
        # Cash and assets
        if any(keyword in name_lower for keyword in ['cash', 'liquidity']):
            return 'cash', 0.85, ['cash', 'liquidity']
        if any(keyword in name_lower for keyword in ['asset', 'assets']):
            if 'total' in name_lower:
                return 'total_assets', 0.8, ['total assets']
            elif 'fixed' in name_lower or 'ppe' in name_lower:
                return 'fixed_assets', 0.8, ['fixed assets', 'ppe']
            return 'assets', 0.6, []
        
        # Working capital and debt
        if 'working capital' in name_lower or 'wc' in name_lower:
            return 'working_capital', 0.9, ['working capital', 'wc']
        if any(keyword in name_lower for keyword in ['debt', 'liabilities']):
            return 'net_debt', 0.7, ['debt', 'liabilities']
        
        # Equity
        if any(keyword in name_lower for keyword in ['equity', 'shareholders']):
            return 'equity', 0.8, ['equity', 'shareholders equity']
        
        # Default unknown category
        return 'unknown', 0.1, []
    
    def discover_measures_from_model(self, 
                                   workspace_name: str = None, 
                                   dataset_name: str = None,
                                   force_refresh: bool = False) -> Dict[str, DiscoveredMeasure]:
        """Discover measures directly from Power BI model"""
        workspace_name = workspace_name or settings.default_workspace_name
        dataset_name = dataset_name or settings.default_dataset_name
        
        # Cache disabled - always get fresh measures
        # Always refresh to ensure latest data from Power BI model
        
        try:
            mcp_logger.info(f"Discovering measures from {workspace_name}/{dataset_name}")
            client = get_powerbi_client()
            
            # Get workspace and dataset
            workspace = client.get_workspace_by_name(workspace_name)
            dataset = client.get_dataset_by_name(workspace['id'], dataset_name)
            
            discovered_measures = {}
            
            try:
                # Use the 4 DAX queries to understand model structure
                mcp_logger.info("Using new discovery method with 4 DAX queries")
                
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
                
                # Query 3: Get Measures (main query for our purpose)
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
                
                # Execute measures query (most important for this function)
                measures_result = client.execute_dax_query(
                    workspace['id'], dataset['id'], measures_query
                )
                
                # Parse measures from result - Handle both result formats
                mcp_logger.info(f"Measures result format: {type(measures_result)}")
                mcp_logger.info(f"Measures result sample: {str(measures_result)[:500]}...")
                
                # Try the custom DAX result format first (list with rows)
                if isinstance(measures_result, list) and len(measures_result) > 0:
                    first_result = measures_result[0]
                    if 'rows' in first_result:
                        rows = first_result['rows']
                        mcp_logger.info(f"✅ Found {len(rows)} total measures using custom DAX format")
                        
                        for row in rows:
                            measure_name = row.get('__def_Measures[Name]', '')
                            description = row.get('__def_Measures[Description]', '')
                            display_folder = row.get('__def_Measures[DisplayFolder]', '')
                            
                            mcp_logger.debug(f"Processing measure: {measure_name}")
                            
                            # Only include measures that have "_AI" in their actual measure name
                            # This indicates they are designed for AI use
                            if measure_name and "_AI" in measure_name:
                                mcp_logger.debug(f"✅ AI-enabled measure found: {measure_name}")
                                
                                # Categorize measure based on name and description
                                combined_text = f"{measure_name} {description}".lower()
                                category, confidence, aliases = self._categorize_measure(measure_name, combined_text)
                                
                                discovered_measures[measure_name] = DiscoveredMeasure(
                                    name=measure_name,
                                    formula=description,  # Use description as formula placeholder
                                    category=category,
                                    confidence=confidence,
                                    aliases=aliases
                                )
                            elif measure_name:
                                mcp_logger.debug(f"⏭️ Skipping non-AI measure: {measure_name}")
                        
                        mcp_logger.info(f"✅ Successfully parsed {len(discovered_measures)} AI-enabled measures from custom DAX format")
                    else:
                        mcp_logger.warning(f"❌ No 'rows' key found in first result: {first_result}")
                else:
                    mcp_logger.warning(f"❌ Result is not a list or is empty: {measures_result}")
                
                # Fallback to original result format
                if not discovered_measures and isinstance(measures_result, dict) and 'results' in measures_result:
                    tables = measures_result['results'][0].get('tables', [])
                    if tables and 'rows' in tables[0]:
                        rows = tables[0]['rows']
                        mcp_logger.info(f"Found {len(rows)} total measures using original format")
                        
                        for row in rows:
                            measure_name = row.get('__def_Measures[Name]', '')
                            description = row.get('__def_Measures[Description]', '')
                            display_folder = row.get('__def_Measures[DisplayFolder]', '')
                            
                            # Only include measures that have "_AI" in their actual measure name
                            # This indicates they are designed for AI use
                            if measure_name and "_AI" in measure_name:
                                mcp_logger.debug(f"✅ AI-enabled measure found: {measure_name}")
                                
                                # Categorize measure based on name and description
                                combined_text = f"{measure_name} {description}".lower()
                                category, confidence, aliases = self._categorize_measure(measure_name, combined_text)
                                
                                discovered_measures[measure_name] = DiscoveredMeasure(
                                    name=measure_name,
                                    formula=description,  # Use description as formula placeholder
                                    category=category,
                                    confidence=confidence,
                                    aliases=aliases
                                )
                            elif measure_name:
                                mcp_logger.debug(f"⏭️ Skipping non-AI measure: {measure_name}")
                else:
                    mcp_logger.warning(f"Unexpected measures result format: {type(measures_result)} - {str(measures_result)[:200]}...")
                
                # Optionally execute other queries for context (but not strictly needed for measures)
                try:
                    # Execute tables query for additional context
                    tables_result = client.execute_dax_query(
                        workspace['id'], dataset['id'], tables_query
                    )
                    mcp_logger.debug(f"Tables query executed successfully")
                    
                    # Execute columns query for additional context
                    columns_result = client.execute_dax_query(
                        workspace['id'], dataset['id'], columns_query  
                    )
                    mcp_logger.debug(f"Columns query executed successfully")
                    
                    # Execute relationships query for additional context
                    relationships_result = client.execute_dax_query(
                        workspace['id'], dataset['id'], relationships_query
                    )
                    mcp_logger.debug(f"Relationships query executed successfully")
                    
                except Exception as e:
                    mcp_logger.warning(f"Additional discovery queries failed (non-critical): {e}")
                
                self._cached_measures = discovered_measures
                self._last_discovery = datetime.now()
                self._save_cache()
                
                if discovered_measures:
                    mcp_logger.info(f"✅ Successfully discovered {len(discovered_measures)} AI-enabled measures using new DAX queries")
                else:
                    mcp_logger.warning("No AI-enabled measures discovered from DAX queries (measures without '_AI' in description were filtered out)")
                    mcp_logger.debug(f"Raw measures result was: {measures_result}")
                return discovered_measures
                
            except Exception as e:
                mcp_logger.error(f"Failed to discover measures using DAX queries: {e}")
                return {}
                
        except Exception as e:
            mcp_logger.error(f"Failed to discover measures: {e}")
            return {}
    
    def get_measure_mapping(self, generic_name: str) -> Optional[str]:
        """Get actual measure name for a generic measure name"""
        
        # 1. Check custom mappings first
        if generic_name in self._measure_mappings:
            return self._measure_mappings[generic_name]
        
        # 2. Check discovered measures by category
        for measure in self._cached_measures.values():
            if measure.category == generic_name and measure.confidence > 0.6:
                return measure.name
        
        # 3. Check aliases
        for measure in self._cached_measures.values():
            if any(alias in generic_name.lower() for alias in measure.aliases):
                return measure.name
        
        # 4. Fallback to generic mapping from constants
        if generic_name in FINANCIAL_MEASURES:
            return FINANCIAL_MEASURES[generic_name].get('dax', f'[{generic_name}]')
        
        return None
    
    def get_all_discovered_measures(self) -> Dict[str, DiscoveredMeasure]:
        """Get all discovered measures"""
        return self._cached_measures.copy()
    
    def get_revenue_measures(self) -> List[str]:
        """Get all measures that appear to be revenue-related"""
        return [
            measure.name for measure in self._cached_measures.values()
            if measure.category in ['revenue'] or 'revenue' in measure.name.lower()
        ]
    
    def get_high_confidence_measures(self, min_confidence: float = 0.7) -> Dict[str, DiscoveredMeasure]:
        """Get measures with high confidence categorization"""
        return {
            name: measure for name, measure in self._cached_measures.items()
            if measure.confidence >= min_confidence
        }
    
    def create_updated_constants(self) -> Dict[str, Any]:
        """Create updated constants with discovered measures"""
        updated_measures = FINANCIAL_MEASURES.copy()
        
        # Update DAX references based on discovered measures
        for generic_name in updated_measures:
            actual_measure = self.get_measure_mapping(generic_name)
            if actual_measure and actual_measure != updated_measures[generic_name].get('dax'):
                updated_measures[generic_name] = updated_measures[generic_name].copy()
                updated_measures[generic_name]['dax'] = f'[{actual_measure}]'
                updated_measures[generic_name]['discovered'] = True
        
        return {
            'FINANCIAL_MEASURES': updated_measures,
            'DISCOVERED_MEASURES': {
                name: {
                    'name': measure.name,
                    'category': measure.category,
                    'confidence': measure.confidence,
                    'aliases': measure.aliases
                }
                for name, measure in self._cached_measures.items()
            },
            'DISCOVERY_METADATA': {
                'last_discovery': self._last_discovery.isoformat() if self._last_discovery else None,
                'total_measures': len(self._cached_measures),
                'high_confidence_count': len(self.get_high_confidence_measures()),
                'revenue_measures': self.get_revenue_measures()
            }
        }
    
    def save_custom_mapping(self, generic_name: str, actual_measure_name: str) -> bool:
        """Save a custom mapping between generic and actual measure names"""
        try:
            self._measure_mappings[generic_name] = actual_measure_name
            
            with open(self.mapping_file, 'w') as f:
                json.dump(self._measure_mappings, f, indent=2)
            
            mcp_logger.info(f"Saved custom mapping: {generic_name} -> {actual_measure_name}")
            return True
        except Exception as e:
            mcp_logger.error(f"Could not save custom mapping: {e}")
            return False


# Global instance
dynamic_measure_manager = DynamicMeasureManager()