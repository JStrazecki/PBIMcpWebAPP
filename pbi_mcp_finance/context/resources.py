"""
FastMCP Resources for automatic Power BI context injection
These resources automatically provide Power BI model context to Claude at conversation start
"""

from fastmcp import FastMCP
from typing import Dict, Any
import asyncio
import threading

from .builder import powerbi_context_builder
from ..utils.logging import mcp_logger
from ..config.settings import settings


def register_context_resources(mcp: FastMCP):
    """Register Power BI context resources for automatic injection"""
    
    @mcp.resource("powerbi://complete-context")
    def get_complete_powerbi_context() -> Dict[str, Any]:
        """
        Power BI context resource - automatically discovers model if defaults available,
        otherwise provides guidance for model selection.
        
        Ensures LLM always has access to discovered measures, tables, and relationships
        to prevent recreation of existing measures.
        """
        try:
            mcp_logger.info("Providing Power BI complete context")
            
            # Check if user has default configuration
            default_workspace = settings.default_workspace_name
            default_dataset = settings.default_dataset_name
            has_defaults = bool(default_workspace and default_dataset)
            
            context = {}
            
            # ALWAYS require explicit model selection - no auto-discovery
            # This ensures LLM always asks user to select workspace/dataset first
            context = self._build_guidance_context(has_defaults, default_workspace, default_dataset)
            context['model_selection_required'] = True
            context['auto_discovery_disabled'] = True
            context['strict_workflow_required'] = True
            
            # Always try to include available measures context even if main discovery fails
            try:
                measures_context = powerbi_context_builder.build_measures_context()
                if measures_context and measures_context.get('measures'):
                    context['available_measures'] = measures_context
            except Exception as measures_error:
                mcp_logger.debug(f"Could not include measures context: {measures_error}")
            
            mcp_logger.info("📋 Power BI context provided successfully")
            return context
            
        except Exception as e:
            mcp_logger.error(f"Failed to build complete Power BI context: {e}")
            return {
                'error': 'Complete context failed',
                'fallback': 'Use select_powerbi_model() tool to begin model selection',
                'error_details': str(e)
            }
    
    def _build_guidance_context(self, has_defaults: bool, default_workspace: str, default_dataset: str) -> Dict[str, Any]:
        """Build guidance context for model selection"""
        context = {
            'model_selection_required': True,
            'FIRST_RESPONSE_REQUIRED': 'Always start with select_powerbi_model() to show simple workspace list',
            'instruction': 'MANDATORY: The VERY FIRST response to ANY query must ONLY be select_powerbi_model() tool. No other tools, no analysis, no suggestions until model is selected.',
            'critical_rules': {
                'rule_1': 'First response MUST be select_powerbi_model() tool - NO exceptions',  
                'rule_2': 'Show workspaces with models - NO suggestions, NO recommendations',
                'rule_3': 'NEVER suggest which model to use - let user choose',
                'rule_4': 'Ask "Which model would you like to choose? Do you want me to proceed with [user question]?"'
            },
            'available_tools': {
                'select_powerbi_model': 'Shows available workspaces and guides model selection',
                'discover_model': 'Runs complete discovery for specified workspace/dataset'
            },
            'default_config': {
                'available': has_defaults,
                'workspace': default_workspace if has_defaults else None,
                'dataset': default_dataset if has_defaults else None,
                'usage': 'Say "Use default model" to use these settings' if has_defaults else None
            },
            'discovery_functions': {
                'auto_discover_workspace_info': 'Get workspace and dataset information',
                'auto_discover_measures': 'Discover and categorize all measures',
                'auto_discover_schema': 'Analyze model schema and table structure',
                'auto_discover_financial_hierarchy': 'Analyze financial hierarchy (lvl1-lvl4)'
            },
            'cache_info': {
                'duration': '6 hours',
                'refresh_option': 'Use force_refresh=True to override cache',
                'automatic_refresh': 'Cache refreshes automatically when expired'
            }
        }
        
        # Add resource metadata
        context['_resource_info'] = {
            'resource_type': 'powerbi_model_selection_guidance',
            'auto_injected': True,
            'requires_user_input': True,
            'workflow': 'select_powerbi_model() → discover_model(workspace, dataset)',
            'usage': 'Interactive model selection and discovery process'
        }
        
        return context
    
    @mcp.resource("powerbi://measures")
    def get_measures_context() -> Dict[str, Any]:
        """
        ⚠️ CRITICAL: Power BI measures context - ALWAYS USE EXISTING MEASURES!
        
        This context provides ALL discovered measures to prevent recreation.
        NEVER create new measures when existing ones are available.
        
        Provides:
        - ALL discovered measures with exact names for DAX queries
        - Measure mappings for revenue, profit, EBITDA, etc.
        - High-confidence measure recommendations
        - MANDATORY: Check this context before any financial calculations
        """
        try:
            mcp_logger.debug("Providing measures context - CRITICAL for preventing measure recreation")
            context = powerbi_context_builder.build_measures_context()
            
            # Add critical warnings about using existing measures
            context['CRITICAL_WARNING'] = {
                'message': 'ALWAYS use existing measures - NEVER recreate what already exists',
                'instruction_1': 'Check discovered_measures section before any calculations',
                'instruction_2': 'Use exact measure names in DAX queries',
                'instruction_3': 'If revenue/profit requested, use existing measures first'
            }
            
            context['_resource_info'] = {
                'resource_type': 'powerbi_measures',
                'replaces_tool': 'discover_measures()',
                'priority': 'HIGHEST - Check before any financial analysis',
                'usage': 'Use measures.active_mappings for generic→actual name conversions'
            }
            
            return context
            
        except Exception as e:
            mcp_logger.error(f"Failed to build measures context: {e}")
            return {'error': 'Measures context unavailable', 'fallback': 'discover_measures()'}
    
    @mcp.resource("powerbi://schema")
    def get_schema_context() -> Dict[str, Any]:
        """
        Power BI model schema context - _Date table is MOST IMPORTANT for date filtering.
        
        Provides:
        - CRITICAL: _Date table syntax for proper date filtering
        - Table name corrections (Date → _Date is common)
        - Fact vs dimension table categorization  
        - Key relationships for financial analysis
        - DAX best practices for date filtering
        """
        try:
            mcp_logger.debug("Providing schema context with _Date table priority")
            context = powerbi_context_builder.build_schema_context()
            
            # Add special emphasis on _Date table
            context['DATE_TABLE_PRIORITY'] = {
                'most_important_table': '_Date',
                'common_error': 'Using Date instead of _Date',
                'correct_syntax': "YEAR(_Date[Date]) = 2024",
                'incorrect_syntax': "YEAR(Date[Date]) = 2024",
                'note': '_Date table contains the proper date dimension for filtering'
            }
            
            context['_resource_info'] = {
                'resource_type': 'powerbi_schema',  
                'replaces_tool': 'analyze_model_schema()',
                'priority': 'HIGH - _Date table syntax is critical for date filtering',
                'usage': 'ALWAYS use _Date table for date filtering, not Date table'
            }
            
            return context
            
        except Exception as e:
            mcp_logger.error(f"Failed to build schema context: {e}")
            return {'error': 'Schema context unavailable', 'fallback': 'analyze_model_schema()'}
    
    @mcp.resource("powerbi://financial-hierarchy")
    def get_financial_hierarchy_context() -> Dict[str, Any]:
        """
        Financial statement hierarchy context (Mapping table structure).
        
        Provides:
        - Mapping table lvl1-lvl4 hierarchy information
        - EBITDA vs Below EBITDA classification guidance
        - Financial analysis best practices
        """
        try:
            mcp_logger.debug("Providing financial hierarchy context")
            context = powerbi_context_builder.build_financial_hierarchy_context()
            
            context['_resource_info'] = {
                'resource_type': 'powerbi_financial_hierarchy',
                'replaces_tool': 'analyze_mapping_structure()',
                'usage': 'Use for proper P&L categorization and EBITDA analysis'
            }
            
            return context
            
        except Exception as e:
            mcp_logger.error(f"Failed to build hierarchy context: {e}")
            return {'error': 'Hierarchy context unavailable', 'fallback': 'analyze_mapping_structure()'}
    
    @mcp.resource("powerbi://quick-reference") 
    def get_quick_reference() -> Dict[str, Any]:
        """
        Quick reference guide for Power BI interactions.
        
        Provides condensed guidance for immediate use without querying tools.
        """
        try:
            # Get current mappings for quick reference
            measures_context = powerbi_context_builder.build_measures_context()
            schema_context = powerbi_context_builder.build_schema_context()
            
            quick_ref = {
                'workspace': powerbi_context_builder.workspace_name,
                'dataset': powerbi_context_builder.dataset_name,
                
                # Most important mappings
                'top_measure_mappings': dict(list(measures_context.get('active_mappings', {}).items())[:10]),
                
                # Most important table corrections  
                'key_table_corrections': schema_context.get('table_name_corrections', {}),
                
                # Essential guidance
                'dax_essentials': {
                    'measure_format': '[ActualMeasureName] - always use brackets',
                    'table_format': 'TableName[ColumnName] - use corrected table names',
                    'date_table': schema_context.get('key_tables', {}).get('date_table', {}).get('name', '_Date'),
                    'fact_table': schema_context.get('key_tables', {}).get('main_fact_table', {}).get('name', 'Journals')
                },
                
                # Tools for model selection and discovery
                'discovery_tools': {
                    'model_selection': 'select_powerbi_model() - Choose workspace and dataset',
                    'complete_discovery': 'discover_model(workspace, dataset) - Run all discovery functions',
                    'individual_discovery': 'auto_discover_measures(), auto_discover_schema(), auto_discover_workspace_info()',
                    'custom_mappings': 'configure_measure_mappings(...) - Custom measure mappings'
                }
            }
            
            return quick_ref
            
        except Exception as e:
            mcp_logger.error(f"Failed to build quick reference: {e}")
            return {'error': 'Quick reference unavailable'}
    
    # Log successful registration
    mcp_logger.info("Registered Power BI context resources with USER-DRIVEN DISCOVERY:")
    mcp_logger.info("  📋 powerbi://complete-context - Guides user through model selection")
    mcp_logger.info("    • Prompts user to select workspace and dataset")
    mcp_logger.info("    • Provides interactive discovery workflow")
    mcp_logger.info("    • No hardcoded model assumptions")
    mcp_logger.info("  📊 powerbi://measures - Discovered measures & mappings (after selection)")
    mcp_logger.info("  🏗️ powerbi://schema - Table schema & corrections (after selection)")
    mcp_logger.info("  🏛️ powerbi://financial-hierarchy - Mapping table structure (after selection)")
    mcp_logger.info("  📋 powerbi://quick-reference - Essential reference guide")
    mcp_logger.info("🎯 USER-DRIVEN: Claude asks user to select model before discovery!")
    mcp_logger.info("🎯 INTERACTIVE: No automatic execution - user-controlled process!")