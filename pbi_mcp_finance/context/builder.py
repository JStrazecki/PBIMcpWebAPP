"""
Context builder for Power BI model information
Creates comprehensive context data for automatic injection into Claude conversations
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from ..config.settings import settings
from ..config.dynamic_measures import dynamic_measure_manager
from ..config.model_schema import model_schema_manager
from ..config.constants import FINANCIAL_MEASURES, POHODA_TABLES
from ..utils.logging import mcp_logger
from ..database.connection import db_manager


class PowerBIContextBuilder:
    """Builds comprehensive Power BI context for Claude conversations with SQLite caching"""
    
    def __init__(self):
        self.workspace_name = settings.default_workspace_name
        self.dataset_name = settings.default_dataset_name
        self.context_db_path = settings.shared_dir / 'context_cache.sqlite'
        self._ensure_context_tables()
    
    def build_measures_context(self) -> Dict[str, Any]:
        """Build measures context with discovered measures and mappings"""
        try:
            # Get discovered measures (from cache if available)
            discovered_measures = dynamic_measure_manager.get_all_discovered_measures()
            high_confidence = dynamic_measure_manager.get_high_confidence_measures()
            revenue_measures = dynamic_measure_manager.get_revenue_measures()
            
            # Build measure mappings
            mappings = {}
            for generic_name in FINANCIAL_MEASURES.keys():
                actual_measure = dynamic_measure_manager.get_measure_mapping(generic_name)
                if actual_measure:
                    mappings[generic_name] = actual_measure
            
            # Categorize measures by type
            categorized_measures = {
                'revenue': [],
                'profitability': [],
                'balance_sheet': [],
                'variance': [],
                'unknown': []
            }
            
            for measure in discovered_measures.values():
                category_group = 'unknown'
                if measure.category in ['revenue']:
                    category_group = 'revenue'
                elif measure.category in ['gross_profit', 'ebitda', 'net_profit']:
                    category_group = 'profitability'
                elif measure.category in ['cash', 'working_capital', 'total_assets', 'equity']:
                    category_group = 'balance_sheet'
                elif 'py' in measure.category or 'budget' in measure.category:
                    category_group = 'variance'
                
                categorized_measures[category_group].append({
                    'name': measure.name,
                    'category': measure.category,
                    'confidence': measure.confidence,
                    'aliases': measure.aliases
                })
            
            context = {
                'workspace': self.workspace_name,
                'dataset': self.dataset_name,
                'last_updated': datetime.now().isoformat(),
                'total_measures': len(discovered_measures),
                'high_confidence_count': len(high_confidence),
                
                # Discovered measures organized by category
                'measures_by_category': categorized_measures,
                
                # Key mappings (generic name -> actual measure)
                'active_mappings': mappings,
                
                # High-confidence measures for quick reference
                'recommended_measures': {
                    measure.name: {
                        'category': measure.category,
                        'confidence': int(measure.confidence * 100),
                        'suggested_use': f"Use [{measure.name}] for {measure.category} queries"
                    }
                    for measure in high_confidence.values()
                },
                
                # Usage instructions
                'usage_guide': {
                    'revenue_queries': revenue_measures[:3] if revenue_measures else [],
                    'dax_format': 'Always use [MeasureName] format in DAX queries',
                    'mapping_info': f'{len(mappings)} generic measures mapped to actual names'
                }
            }
            
            # Cache context for performance
            self._cache_context('measures', context)
            return context
            
        except Exception as e:
            mcp_logger.warning(f"Could not build measures context: {e}")
            return {
                'error': 'Measures context unavailable',
                'fallback': 'Use discover_measures() tool to get current measure list',
                'workspace': self.workspace_name,
                'dataset': self.dataset_name
            }
    
    def build_schema_context(self) -> Dict[str, Any]:
        """Build schema context with table/column corrections"""
        try:
            # Get discovered schema
            discovered_tables = model_schema_manager._cached_tables
            fact_tables = model_schema_manager.get_fact_tables()
            dim_tables = model_schema_manager.get_dimension_tables()
            
            # Common table name corrections
            corrections = {}
            common_names = ['date', 'period', 'scenario', 'accounts', 'journals', 'mapping']
            for name in common_names:
                corrected = model_schema_manager.get_corrected_table_name(name)
                if corrected and corrected.lower() != name:
                    corrections[name.title()] = corrected
            
            # Key table information
            key_tables = {}
            if fact_tables:
                main_fact = max(fact_tables, key=lambda t: t.confidence)
                key_tables['main_fact_table'] = {
                    'name': main_fact.name,
                    'columns': len(main_fact.columns),
                    'confidence': int(main_fact.confidence * 100)
                }
            
            # Date table
            date_tables = [t for t in dim_tables if 'date' in t.name.lower()]
            if date_tables:
                date_table = date_tables[0]
                key_tables['date_table'] = {
                    'name': date_table.name,
                    'year_columns': [col for col in date_table.columns if 'year' in col.lower()]
                }
            
            # Mapping table
            mapping_tables = [t for t in discovered_tables.values() if 'mapping' in t.name.lower()]
            if mapping_tables:
                mapping_table = mapping_tables[0]
                key_tables['mapping_table'] = {
                    'name': mapping_table.name,
                    'hierarchy_columns': [col for col in mapping_table.columns if col.startswith('lvl')]
                }
            
            context = {
                'workspace': self.workspace_name,
                'dataset': self.dataset_name,
                'last_updated': datetime.now().isoformat(),
                'total_tables': len(discovered_tables),
                
                # Table corrections for common DAX errors
                'table_name_corrections': corrections,
                
                # Key tables for financial analysis
                'key_tables': key_tables,
                
                # Table categorization
                'fact_tables': [t.name for t in fact_tables],
                'dimension_tables': [t.name for t in dim_tables],
                
                # DAX query guidance
                'dax_best_practices': {
                    'table_references': 'Always use actual table names from corrections above',
                    'common_errors': [
                        "Use '_Date[Year]' not 'Date[Year]'",
                        "Use 'Journals' for transaction data",
                        "Use 'Mapping' table for financial hierarchy (lvl1-lvl4)"
                    ]
                }
            }
            
            # Cache context for performance
            self._cache_context('schema', context)
            return context
            
        except Exception as e:
            mcp_logger.warning(f"Could not build schema context: {e}")
            return {
                'error': 'Schema context unavailable',
                'fallback': 'Use analyze_model_schema() tool to get current schema',
                'static_info': POHODA_TABLES
            }
    
    def build_financial_hierarchy_context(self) -> Dict[str, Any]:
        """Build context for financial statement hierarchy (Mapping table)"""
        try:
            context = {
                'mapping_table_info': {
                    'description': 'CRITICAL for financial analysis - provides EBITDA vs Below EBITDA classification',
                    'key_columns': ['Account Id', 'Account Code', 'Account Name', 'lvl1', 'lvl2', 'lvl3', 'lvl4'],
                    'hierarchy_levels': {
                        'lvl1': 'Top level - EBITDA or Below EBITDA classification',
                        'lvl2': 'Secondary classification - detailed financial categories',
                        'lvl3': 'Tertiary classification - specific line items', 
                        'lvl4': 'Most detailed level - granular account classification'
                    },
                    'usage': 'Essential for P&L analysis, financial statement categorization, and EBITDA calculations'
                },
                
                'financial_analysis_guide': {
                    'revenue_classification': 'Use lvl1=EBITDA accounts for revenue analysis',
                    'cost_analysis': 'Use lvl1=Below EBITDA for cost categorization',
                    'hierarchy_queries': 'Always include relevant lvl1-lvl4 columns for proper categorization'
                }
            }
            
            # Cache context for performance
            self._cache_context('financial_hierarchy', context)
            return context
            
        except Exception as e:
            mcp_logger.warning(f"Could not build hierarchy context: {e}")
            return {
                'error': 'Hierarchy context unavailable', 
                'static_info': POHODA_TABLES.get('Mapping', {})
            }
    
    def build_complete_context(self) -> Dict[str, Any]:
        """Build complete Power BI context for Claude"""
        try:
            mcp_logger.info("Building complete Power BI context for Claude injection")
            
            context = {
                'power_bi_model_info': {
                    'workspace': self.workspace_name,
                    'dataset': self.dataset_name,
                    'last_context_update': datetime.now().isoformat(),
                    'context_version': '1.0'
                },
                
                # Core components
                'measures': self.build_measures_context(),
                'schema': self.build_schema_context(), 
                'financial_hierarchy': self.build_financial_hierarchy_context(),
                
                # Quick reference for Claude
                'claude_quick_reference': {
                    'measure_format': 'Use [MeasureName] format in all DAX queries',
                    'table_corrections': 'Check schema.table_name_corrections for actual table names',
                    'financial_hierarchy': 'Use Mapping table lvl1-lvl4 for proper P&L categorization',
                    'best_practices': [
                        'Always use actual measure names from measures.active_mappings',
                        'Use corrected table names to avoid DAX errors',
                        'Include financial hierarchy for accurate analysis',
                        'Give short and precise answers unless asked otherwise'
                    ]
                },
                
                # Performance info
                'context_metadata': {
                    'cache_duration': '24 hours',
                    'refresh_command': 'Use discover_measures(force_refresh=True) to update',
                    'schema_refresh': 'Use analyze_model_schema(force_refresh=True) to update'
                }
            }
            
            mcp_logger.info(f"Context built successfully: {len(context['measures'].get('active_mappings', {}))} measure mappings, {len(context['schema'].get('table_name_corrections', {}))} table corrections")
            
            return context
            
        except Exception as e:
            mcp_logger.error(f"Failed to build complete context: {e}")
            return {
                'error': 'Complete context unavailable',
                'fallback_tools': [
                    'discover_measures() - Get current measures',
                    'analyze_model_schema() - Get table schema', 
                    'analyze_mapping_structure() - Get financial hierarchy'
                ],
                'workspace': self.workspace_name,
                'dataset': self.dataset_name
            }
    
    def get_context_summary(self) -> str:
        """Get a human-readable summary of available context"""
        try:
            context = self.build_complete_context()
            
            if 'error' in context:
                return f"❌ Context Error: {context['error']}"
            
            measures_count = context['measures'].get('total_measures', 0)
            mappings_count = len(context['measures'].get('active_mappings', {}))
            tables_count = context['schema'].get('total_tables', 0)
            corrections_count = len(context['schema'].get('table_name_corrections', {}))
            
            summary = f"""
📊 Power BI Context Ready:
• Workspace: {self.workspace_name}
• Dataset: {self.dataset_name}
• Discovered Measures: {measures_count} ({mappings_count} mapped)
• Schema Tables: {tables_count} ({corrections_count} corrections)
• Financial Hierarchy: Available
• Last Updated: {datetime.now().strftime('%H:%M:%S')}

✅ Claude has full model context - no discovery queries needed!
"""
            return summary.strip()
            
        except Exception as e:
            return f"❌ Context Summary Error: {e}"


    def _ensure_context_tables(self):
        """Create context cache tables if they don't exist"""
        try:
            create_tables_sql = """
            CREATE TABLE IF NOT EXISTS context_cache (
                id TEXT PRIMARY KEY,
                context_type TEXT NOT NULL,
                workspace TEXT NOT NULL,
                dataset TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                context_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                hit_count INTEGER DEFAULT 0,
                last_accessed TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS context_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_type TEXT NOT NULL,
                operation TEXT NOT NULL,
                execution_time_ms INTEGER NOT NULL,
                cache_hit BOOLEAN NOT NULL,
                timestamp TEXT NOT NULL,
                workspace TEXT NOT NULL,
                dataset TEXT NOT NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_context_cache_type_workspace 
                ON context_cache(context_type, workspace, dataset);
            CREATE INDEX IF NOT EXISTS idx_context_cache_expires 
                ON context_cache(expires_at);
            CREATE INDEX IF NOT EXISTS idx_performance_timestamp 
                ON context_performance(timestamp);
            """
            
            db_manager.execute_script(self.context_db_path, create_tables_sql)
            mcp_logger.debug("Context cache tables ensured")
            
        except Exception as e:
            mcp_logger.warning(f"Failed to create context cache tables: {e}")
    
    def _get_context_id(self, context_type: str) -> str:
        """Generate unique context ID"""
        return f"{context_type}_{self.workspace_name}_{self.dataset_name}"
    
    def _get_content_hash(self, data: Dict[str, Any]) -> str:
        """Generate hash of context content for change detection"""
        content_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _cache_context(self, context_type: str, context_data: Dict[str, Any], ttl_hours: int = 24):
        """Cache context data with TTL"""
        try:
            context_id = self._get_context_id(context_type)
            content_hash = self._get_content_hash(context_data)
            now = datetime.now()
            expires_at = now + timedelta(hours=ttl_hours)
            
            insert_sql = """
            INSERT OR REPLACE INTO context_cache 
            (id, context_type, workspace, dataset, content_hash, context_data, 
             created_at, expires_at, hit_count, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """
            
            db_manager.execute_command(
                self.context_db_path, 
                insert_sql,
                (context_id, context_type, self.workspace_name, self.dataset_name,
                 content_hash, json.dumps(context_data), now.isoformat(), 
                 expires_at.isoformat(), now.isoformat())
            )
            
        except Exception as e:
            mcp_logger.warning(f"Failed to cache {context_type} context: {e}")
    
    def _get_cached_context(self, context_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached context if valid"""
        try:
            context_id = self._get_context_id(context_type)
            now = datetime.now().isoformat()
            
            select_sql = """
            SELECT context_data, content_hash, created_at 
            FROM context_cache 
            WHERE id = ? AND expires_at > ?
            """
            
            results = db_manager.execute_query(
                self.context_db_path, 
                select_sql, 
                (context_id, now)
            )
            
            if results:
                # Update hit count and last accessed
                update_sql = """
                UPDATE context_cache 
                SET hit_count = hit_count + 1, last_accessed = ? 
                WHERE id = ?
                """
                db_manager.execute_command(
                    self.context_db_path, 
                    update_sql, 
                    (now, context_id)
                )
                
                return json.loads(results[0]['context_data'])
            
        except Exception as e:
            mcp_logger.warning(f"Failed to retrieve cached {context_type} context: {e}")
        
        return None
    
    def _log_performance(self, context_type: str, operation: str, 
                        execution_time_ms: int, cache_hit: bool):
        """Log context operation performance"""
        try:
            insert_sql = """
            INSERT INTO context_performance 
            (context_type, operation, execution_time_ms, cache_hit, timestamp, workspace, dataset)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            db_manager.execute_command(
                self.context_db_path,
                insert_sql,
                (context_type, operation, execution_time_ms, cache_hit, 
                 datetime.now().isoformat(), self.workspace_name, self.dataset_name)
            )
            
        except Exception as e:
            mcp_logger.warning(f"Failed to log performance: {e}")
    
    def build_measures_context_cached(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Build measures context with SQLite caching"""
        start_time = datetime.now()
        
        if not force_refresh:
            cached = self._get_cached_context('measures')
            if cached:
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                self._log_performance('measures', 'build', execution_time, True)
                mcp_logger.debug("Measures context served from cache")
                return cached
        
        # Build fresh context
        context = self.build_measures_context()
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        self._log_performance('measures', 'build', execution_time, False)
        
        return context
    
    def build_schema_context_cached(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Build schema context with SQLite caching"""
        start_time = datetime.now()
        
        if not force_refresh:
            cached = self._get_cached_context('schema')
            if cached:
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                self._log_performance('schema', 'build', execution_time, True)
                mcp_logger.debug("Schema context served from cache")
                return cached
        
        # Build fresh context
        context = self.build_schema_context()
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        self._log_performance('schema', 'build', execution_time, False)
        
        return context
    
    def build_financial_hierarchy_context_cached(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Build financial hierarchy context with SQLite caching"""
        start_time = datetime.now()
        
        if not force_refresh:
            cached = self._get_cached_context('financial_hierarchy')
            if cached:
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                self._log_performance('financial_hierarchy', 'build', execution_time, True)
                mcp_logger.debug("Financial hierarchy context served from cache")
                return cached
        
        # Build fresh context
        context = self.build_financial_hierarchy_context()
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        self._log_performance('financial_hierarchy', 'build', execution_time, False)
        
        return context
    
    def build_complete_context_optimized(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Build complete context with performance optimizations"""
        start_time = datetime.now()
        
        try:
            mcp_logger.info("Building optimized Power BI context with SQLite caching")
            
            # Use cached versions for better performance
            context = {
                'power_bi_model_info': {
                    'workspace': self.workspace_name,
                    'dataset': self.dataset_name,
                    'last_context_update': datetime.now().isoformat(),
                    'context_version': '2.0',
                    'cache_enabled': True
                },
                
                # Core components with caching
                'measures': self.build_measures_context_cached(force_refresh),
                'schema': self.build_schema_context_cached(force_refresh), 
                'financial_hierarchy': self.build_financial_hierarchy_context_cached(force_refresh),
                
                # Enhanced quick reference
                'claude_quick_reference': {
                    'measure_format': 'Use [MeasureName] format in all DAX queries',
                    'table_corrections': 'Check schema.table_name_corrections for actual table names',
                    'financial_hierarchy': 'Use Mapping table lvl1-lvl4 for proper P&L categorization',
                    'performance_mode': 'Context cached for 24h - use force_refresh=True to update',
                    'best_practices': [
                        'Always use actual measure names from measures.active_mappings',
                        'Use corrected table names to avoid DAX errors',
                        'Include financial hierarchy for accurate analysis',
                        'Give short and precise answers unless asked otherwise'
                    ]
                },
                
                # Enhanced metadata with performance stats
                'context_metadata': self._get_context_metadata()
            }
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            context['context_metadata']['build_time_ms'] = execution_time
            
            self._log_performance('complete', 'build', execution_time, False)
            
            measures_count = len(context['measures'].get('active_mappings', {}))
            tables_count = context['schema'].get('total_tables', 0)
            
            mcp_logger.info(f"Optimized context built in {execution_time}ms: {measures_count} mappings, {tables_count} tables")
            
            return context
            
        except Exception as e:
            mcp_logger.error(f"Failed to build optimized context: {e}")
            # Fallback to original method
            return self.build_complete_context()
    
    def _get_context_metadata(self) -> Dict[str, Any]:
        """Get enhanced context metadata with cache statistics"""
        try:
            # Get cache statistics
            stats_sql = """
            SELECT 
                context_type,
                COUNT(*) as cache_entries,
                SUM(hit_count) as total_hits,
                AVG(hit_count) as avg_hits,
                MAX(last_accessed) as last_access
            FROM context_cache 
            WHERE workspace = ? AND dataset = ?
            GROUP BY context_type
            """
            
            cache_stats = {}
            try:
                results = db_manager.execute_query(
                    self.context_db_path, 
                    stats_sql, 
                    (self.workspace_name, self.dataset_name)
                )
                
                for row in results:
                    cache_stats[row['context_type']] = {
                        'entries': row['cache_entries'],
                        'total_hits': row['total_hits'],
                        'avg_hits': round(row['avg_hits'], 2),
                        'last_access': row['last_access']
                    }
            except Exception:
                cache_stats = {'error': 'Cache stats unavailable'}
            
            # Get performance statistics
            perf_sql = """
            SELECT 
                context_type,
                AVG(execution_time_ms) as avg_time,
                MIN(execution_time_ms) as min_time,
                MAX(execution_time_ms) as max_time,
                SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as cache_hit_rate
            FROM context_performance 
            WHERE workspace = ? AND dataset = ? 
                AND timestamp > datetime('now', '-7 days')
            GROUP BY context_type
            """
            
            perf_stats = {}
            try:
                results = db_manager.execute_query(
                    self.context_db_path, 
                    perf_sql, 
                    (self.workspace_name, self.dataset_name)
                )
                
                for row in results:
                    perf_stats[row['context_type']] = {
                        'avg_time_ms': round(row['avg_time'], 1),
                        'min_time_ms': row['min_time'],
                        'max_time_ms': row['max_time'],
                        'cache_hit_rate': round(row['cache_hit_rate'], 1)
                    }
            except Exception:
                perf_stats = {'error': 'Performance stats unavailable'}
            
            return {
                'cache_duration': '24 hours',
                'cache_statistics': cache_stats,
                'performance_statistics': perf_stats,
                'refresh_command': 'Use build_complete_context_optimized(force_refresh=True)',
                'schema_refresh': 'Use analyze_model_schema(force_refresh=True) to update',
                'database_info': {
                    'cache_db': str(self.context_db_path),
                    'cache_enabled': True,
                    'version': '2.0'
                }
            }
            
        except Exception as e:
            mcp_logger.warning(f"Failed to get context metadata: {e}")
            return {
                'cache_duration': '24 hours',
                'error': str(e),
                'fallback': 'Basic metadata only'
            }
    
    def clear_context_cache(self, context_type: Optional[str] = None) -> Dict[str, Any]:
        """Clear context cache (all or specific type)"""
        try:
            if context_type:
                delete_sql = "DELETE FROM context_cache WHERE context_type = ? AND workspace = ? AND dataset = ?"
                affected = db_manager.execute_command(
                    self.context_db_path, 
                    delete_sql, 
                    (context_type, self.workspace_name, self.dataset_name)
                )
                return {
                    'success': True,
                    'message': f'Cleared {affected} {context_type} cache entries'
                }
            else:
                delete_sql = "DELETE FROM context_cache WHERE workspace = ? AND dataset = ?"
                affected = db_manager.execute_command(
                    self.context_db_path, 
                    delete_sql, 
                    (self.workspace_name, self.dataset_name)
                )
                return {
                    'success': True,
                    'message': f'Cleared all {affected} cache entries'
                }
                
        except Exception as e:
            mcp_logger.error(f"Failed to clear context cache: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_context_cache_info(self) -> Dict[str, Any]:
        """Get detailed context cache information"""
        try:
            info_sql = """
            SELECT 
                context_type,
                created_at,
                expires_at,
                hit_count,
                last_accessed,
                CASE 
                    WHEN expires_at > datetime('now') THEN 'valid'
                    ELSE 'expired'
                END as status,
                LENGTH(context_data) as size_bytes
            FROM context_cache 
            WHERE workspace = ? AND dataset = ?
            ORDER BY context_type, created_at DESC
            """
            
            results = db_manager.execute_query(
                self.context_db_path, 
                info_sql, 
                (self.workspace_name, self.dataset_name)
            )
            
            cache_info = []
            for row in results:
                cache_info.append({
                    'context_type': row['context_type'],
                    'created_at': row['created_at'],
                    'expires_at': row['expires_at'],
                    'hit_count': row['hit_count'],
                    'last_accessed': row['last_accessed'],
                    'status': row['status'],
                    'size_kb': round(row['size_bytes'] / 1024, 2)
                })
            
            return {
                'workspace': self.workspace_name,
                'dataset': self.dataset_name,
                'cache_entries': cache_info,
                'total_entries': len(cache_info),
                'valid_entries': sum(1 for entry in cache_info if entry['status'] == 'valid'),
                'total_size_kb': sum(entry['size_kb'] for entry in cache_info)
            }
            
        except Exception as e:
            mcp_logger.error(f"Failed to get cache info: {e}")
            return {
                'error': str(e),
                'workspace': self.workspace_name,
                'dataset': self.dataset_name
            }


# Global context builder instance
powerbi_context_builder = PowerBIContextBuilder()