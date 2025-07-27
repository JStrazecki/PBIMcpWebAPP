"""
Enhanced logging system with SQLite storage for Power BI MCP Finance Server
Provides structured logging, analysis, and monitoring capabilities
"""

import json
import logging
import logging.handlers
import sys
import threading
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import hashlib
import inspect

from ..config.settings import settings
from ..database.connection import db_manager


class SQLiteLogHandler(logging.Handler):
    """Custom logging handler that stores logs in SQLite database"""
    
    def __init__(self, db_path: Path):
        super().__init__()
        self.db_path = db_path
        self._ensure_log_tables()
        self._lock = threading.Lock()
    
    def _ensure_log_tables(self):
        """Create log tables if they don't exist"""
        try:
            create_tables_sql = """
            CREATE TABLE IF NOT EXISTS log_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                logger_name TEXT NOT NULL,
                module TEXT,
                function TEXT,
                line_number INTEGER,
                message TEXT NOT NULL,
                formatted_message TEXT,
                exception_type TEXT,
                exception_message TEXT,
                stack_trace TEXT,
                extra_data TEXT,
                session_id TEXT,
                thread_id TEXT,
                process_id INTEGER,
                created_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS log_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_name TEXT NOT NULL,
                context_value TEXT NOT NULL,
                log_entry_id INTEGER,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (log_entry_id) REFERENCES log_entries (id)
            );
            
            CREATE TABLE IF NOT EXISTS log_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_hash TEXT UNIQUE NOT NULL,
                pattern_template TEXT NOT NULL,
                first_occurrence TEXT NOT NULL,
                last_occurrence TEXT NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                severity_level TEXT NOT NULL,
                category TEXT,
                is_critical BOOLEAN DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS log_aggregations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aggregation_date TEXT NOT NULL,
                level TEXT NOT NULL,
                logger_name TEXT NOT NULL,
                count INTEGER NOT NULL,
                avg_per_hour REAL,
                peak_hour INTEGER,
                peak_count INTEGER,
                created_at TEXT NOT NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_log_entries_timestamp ON log_entries(timestamp);
            CREATE INDEX IF NOT EXISTS idx_log_entries_level ON log_entries(level);
            CREATE INDEX IF NOT EXISTS idx_log_entries_logger ON log_entries(logger_name);
            CREATE INDEX IF NOT EXISTS idx_log_entries_session ON log_entries(session_id);
            CREATE INDEX IF NOT EXISTS idx_log_patterns_hash ON log_patterns(pattern_hash);
            CREATE INDEX IF NOT EXISTS idx_log_aggregations_date ON log_aggregations(aggregation_date, level);
            """
            
            db_manager.execute_script(self.db_path, create_tables_sql)
            
        except Exception as e:
            # Fallback to stderr if database setup fails
            print(f"Failed to create log tables: {e}", file=sys.stderr)
    
    def emit(self, record: logging.LogRecord):
        """Store log record in SQLite database"""
        try:
            with self._lock:
                self._store_log_record(record)
        except Exception as e:
            # Don't let logging errors break the application
            print(f"Log storage failed: {e}", file=sys.stderr)
    
    def _store_log_record(self, record: logging.LogRecord):
        """Store individual log record"""
        # Format the record
        formatted_message = self.format(record) if self.formatter else record.getMessage()
        
        # Extract exception information
        exception_type = None
        exception_message = None
        stack_trace = None
        if record.exc_info:
            exception_type = record.exc_info[0].__name__ if record.exc_info[0] else None
            exception_message = str(record.exc_info[1]) if record.exc_info[1] else None
            stack_trace = ''.join(traceback.format_exception(*record.exc_info))
        
        # Extract caller information
        module = getattr(record, 'module', record.module) if hasattr(record, 'module') else record.name
        function = getattr(record, 'funcName', None)
        line_number = getattr(record, 'lineno', None)
        
        # Extract extra data
        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info'):
                try:
                    json.dumps(value)  # Test if serializable
                    extra_data[key] = value
                except (TypeError, ValueError):
                    extra_data[key] = str(value)
        
        # Get session ID (could be from context or thread local)
        session_id = getattr(record, 'session_id', None) or self._get_session_id()
        
        # Store main log entry
        insert_sql = """
        INSERT INTO log_entries (
            timestamp, level, logger_name, module, function, line_number,
            message, formatted_message, exception_type, exception_message,
            stack_trace, extra_data, session_id, thread_id, process_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            datetime.fromtimestamp(record.created).isoformat(),
            record.levelname,
            record.name,
            module,
            function,
            line_number,
            record.getMessage(),
            formatted_message,
            exception_type,
            exception_message,
            stack_trace,
            json.dumps(extra_data) if extra_data else None,
            session_id,
            str(record.thread),
            record.process,
            datetime.now().isoformat()
        )
        
        db_manager.execute_command(self.db_path, insert_sql, params)
        
        # Store pattern analysis
        self._analyze_log_pattern(record)
    
    def _get_session_id(self) -> str:
        """Generate or retrieve session ID"""
        # Use thread-local storage for session ID
        if not hasattr(self, '_session_ids'):
            self._session_ids = threading.local()
        
        if not hasattr(self._session_ids, 'current_session'):
            # Generate session ID based on timestamp and thread
            session_data = f"{datetime.now().isoformat()}_{threading.current_thread().ident}"
            self._session_ids.current_session = hashlib.md5(session_data.encode()).hexdigest()[:16]
        
        return self._session_ids.current_session
    
    def _analyze_log_pattern(self, record: logging.LogRecord):
        """Analyze and store log patterns for monitoring"""
        try:
            # Create pattern template by replacing variable parts
            message = record.getMessage()
            pattern_template = self._extract_pattern(message)
            pattern_hash = hashlib.md5(pattern_template.encode()).hexdigest()
            
            now = datetime.now().isoformat()
            
            # Update or insert pattern
            update_sql = """
            UPDATE log_patterns 
            SET last_occurrence = ?, occurrence_count = occurrence_count + 1
            WHERE pattern_hash = ?
            """
            
            affected = db_manager.execute_command(
                self.db_path, update_sql, (now, pattern_hash)
            )
            
            if affected == 0:
                # Insert new pattern
                insert_sql = """
                INSERT INTO log_patterns (
                    pattern_hash, pattern_template, first_occurrence, 
                    last_occurrence, occurrence_count, severity_level, 
                    category, is_critical
                ) VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                """
                
                category = self._categorize_log_message(message)
                is_critical = record.levelno >= logging.ERROR
                
                db_manager.execute_command(
                    self.db_path, insert_sql, 
                    (pattern_hash, pattern_template, now, now, 
                     record.levelname, category, is_critical)
                )
                
        except Exception as e:
            # Don't let pattern analysis break logging
            print(f"Pattern analysis failed: {e}", file=sys.stderr)
    
    def _extract_pattern(self, message: str) -> str:
        """Extract pattern template from log message"""
        import re
        
        # Replace common variable patterns
        patterns = [
            (r'\d+\.\d+', '{float}'),           # Floating point numbers
            (r'\b\d+\b', '{number}'),           # Integers
            (r'\b[0-9a-fA-F]{8,}\b', '{hash}'), # Hash values
            (r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '{timestamp}'), # ISO timestamps
            (r'\b\w+@\w+\.\w+\b', '{email}'),   # Email addresses
            (r'https?://\S+', '{url}'),         # URLs
            (r'/[/\w.-]+', '{path}'),          # File paths
        ]
        
        pattern = message
        for regex, replacement in patterns:
            pattern = re.sub(regex, replacement, pattern)
        
        return pattern
    
    def _categorize_log_message(self, message: str) -> str:
        """Categorize log message for analysis"""
        message_lower = message.lower()
        
        if any(term in message_lower for term in ['auth', 'login', 'token', 'credential']):
            return 'authentication'
        elif any(term in message_lower for term in ['database', 'sql', 'query', 'connection']):
            return 'database'
        elif any(term in message_lower for term in ['api', 'http', 'request', 'response']):
            return 'api'
        elif any(term in message_lower for term in ['powerbi', 'dax', 'measure', 'dataset']):
            return 'powerbi'
        elif any(term in message_lower for term in ['cache', 'context', 'build']):
            return 'caching'
        elif any(term in message_lower for term in ['error', 'exception', 'failed', 'failure']):
            return 'error'
        elif any(term in message_lower for term in ['performance', 'slow', 'timeout']):
            return 'performance'
        else:
            return 'general'


class EnhancedPowerBILogger:
    """Enhanced logger with SQLite storage and analysis capabilities"""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.db_path = settings.shared_dir / 'enhanced_logs.sqlite'
        self._setup_logger(level)
        self._context_stack = []
    
    def _setup_logger(self, level: str):
        """Setup enhanced logger with multiple handlers"""
        if self.logger.handlers:
            return  # Logger already configured
        
        # Set level
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Create enhanced formatter
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Simple formatter for console
        simple_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        
        # Console handler (simple format)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        # SQLite handler (detailed format)
        sqlite_handler = SQLiteLogHandler(self.db_path)
        sqlite_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(sqlite_handler)
        
        # File handler for traditional logs (optional)
        log_dir = Path(__file__).parent.parent.parent / "logs"
        if log_dir.exists() or self._try_create_log_dir(log_dir):
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / f"{self.name.replace('.', '_')}.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)
    
    def _try_create_log_dir(self, log_dir: Path) -> bool:
        """Try to create log directory"""
        try:
            log_dir.mkdir(exist_ok=True)
            return True
        except Exception:
            return False
    
    def with_context(self, **context):
        """Add context to subsequent log messages"""
        return LogContext(self, context)
    
    def debug(self, message: str, **extra):
        self._log_with_extra(logging.DEBUG, message, extra)
    
    def info(self, message: str, **extra):
        self._log_with_extra(logging.INFO, message, extra)
    
    def warning(self, message: str, **extra):
        self._log_with_extra(logging.WARNING, message, extra)
    
    def error(self, message: str, **extra):
        self._log_with_extra(logging.ERROR, message, extra)
    
    def critical(self, message: str, **extra):
        self._log_with_extra(logging.CRITICAL, message, extra)
    
    def _log_with_extra(self, level: int, message: str, extra: Dict[str, Any]):
        """Log message with additional context"""
        # Merge context stack
        merged_extra = {}
        for context in self._context_stack:
            merged_extra.update(context)
        merged_extra.update(extra)
        
        # Add caller information
        frame = inspect.currentframe().f_back.f_back
        merged_extra.update({
            'caller_module': frame.f_globals.get('__name__', 'unknown'),
            'caller_function': frame.f_code.co_name,
            'caller_line': frame.f_lineno
        })
        
        self.logger.log(level, message, extra=merged_extra)
    
    def log_performance(self, operation: str, duration_ms: float, **extra):
        """Log performance metrics"""
        self.info(
            f"Performance: {operation} completed in {duration_ms:.2f}ms",
            operation=operation,
            duration_ms=duration_ms,
            category='performance',
            **extra
        )
    
    def log_api_call(self, endpoint: str, method: str, status_code: int, 
                    duration_ms: float, **extra):
        """Log API call details"""
        self.info(
            f"API Call: {method} {endpoint} -> {status_code} ({duration_ms:.2f}ms)",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            category='api',
            **extra
        )
    
    def log_database_operation(self, operation: str, table: str, affected_rows: int, 
                              duration_ms: float, **extra):
        """Log database operation details"""
        self.info(
            f"Database: {operation} on {table} affected {affected_rows} rows ({duration_ms:.2f}ms)",
            operation=operation,
            table=table,
            affected_rows=affected_rows,
            duration_ms=duration_ms,
            category='database',
            **extra
        )
    
    def log_business_event(self, event_type: str, description: str, **extra):
        """Log business/application events"""
        self.info(
            f"Business Event: {event_type} - {description}",
            event_type=event_type,
            description=description,
            category='business',
            **extra
        )


class LogContext:
    """Context manager for adding context to log messages"""
    
    def __init__(self, logger: EnhancedPowerBILogger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context
    
    def __enter__(self):
        self.logger._context_stack.append(self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger._context_stack.pop()


class LogAnalyzer:
    """Analyze logs stored in SQLite database"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (settings.shared_dir / 'enhanced_logs.sqlite')
    
    def get_log_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get log summary for specified time period"""
        since = datetime.now() - timedelta(hours=hours)
        since_str = since.isoformat()
        
        # Get counts by level
        level_counts_sql = """
        SELECT level, COUNT(*) as count
        FROM log_entries 
        WHERE timestamp > ?
        GROUP BY level
        ORDER BY count DESC
        """
        
        level_counts = {}
        try:
            results = db_manager.execute_query(self.db_path, level_counts_sql, (since_str,))
            level_counts = {row['level']: row['count'] for row in results}
        except Exception:
            level_counts = {'error': 'Unable to fetch level counts'}
        
        # Get top patterns
        patterns_sql = """
        SELECT pattern_template, occurrence_count, severity_level, category
        FROM log_patterns 
        WHERE last_occurrence > ?
        ORDER BY occurrence_count DESC
        LIMIT 10
        """
        
        top_patterns = []
        try:
            results = db_manager.execute_query(self.db_path, patterns_sql, (since_str,))
            top_patterns = [dict(row) for row in results]
        except Exception:
            top_patterns = [{'error': 'Unable to fetch patterns'}]
        
        # Get error summary
        error_summary_sql = """
        SELECT 
            exception_type,
            COUNT(*) as count,
            MAX(timestamp) as last_occurrence
        FROM log_entries 
        WHERE level IN ('ERROR', 'CRITICAL') 
            AND timestamp > ?
            AND exception_type IS NOT NULL
        GROUP BY exception_type
        ORDER BY count DESC
        LIMIT 5
        """
        
        error_summary = []
        try:
            results = db_manager.execute_query(self.db_path, error_summary_sql, (since_str,))
            error_summary = [dict(row) for row in results]
        except Exception:
            error_summary = [{'error': 'Unable to fetch error summary'}]
        
        return {
            'time_period': f'Last {hours} hours',
            'total_entries': sum(level_counts.values()) if isinstance(level_counts, dict) else 0,
            'level_counts': level_counts,
            'top_patterns': top_patterns,
            'error_summary': error_summary,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics from logs"""
        since = datetime.now() - timedelta(hours=hours)
        since_str = since.isoformat()
        
        perf_sql = """
        SELECT 
            JSON_EXTRACT(extra_data, '$.operation') as operation,
            AVG(CAST(JSON_EXTRACT(extra_data, '$.duration_ms') AS REAL)) as avg_duration,
            MIN(CAST(JSON_EXTRACT(extra_data, '$.duration_ms') AS REAL)) as min_duration,
            MAX(CAST(JSON_EXTRACT(extra_data, '$.duration_ms') AS REAL)) as max_duration,
            COUNT(*) as operation_count
        FROM log_entries 
        WHERE timestamp > ? 
            AND JSON_EXTRACT(extra_data, '$.category') = 'performance'
            AND JSON_EXTRACT(extra_data, '$.duration_ms') IS NOT NULL
        GROUP BY JSON_EXTRACT(extra_data, '$.operation')
        ORDER BY avg_duration DESC
        """
        
        try:
            results = db_manager.execute_query(self.db_path, perf_sql, (since_str,))
            performance_data = []
            
            for row in results:
                if row['operation']:  # Skip null operations
                    performance_data.append({
                        'operation': row['operation'],
                        'avg_duration_ms': round(row['avg_duration'], 2),
                        'min_duration_ms': row['min_duration'],
                        'max_duration_ms': row['max_duration'],
                        'operation_count': row['operation_count']
                    })
            
            return {
                'time_period': f'Last {hours} hours',
                'performance_data': performance_data,
                'total_operations': sum(item['operation_count'] for item in performance_data)
            }
            
        except Exception as e:
            return {
                'error': f'Unable to fetch performance metrics: {e}',
                'time_period': f'Last {hours} hours'
            }
    
    def get_error_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """Get detailed error analysis"""
        since = datetime.now() - timedelta(hours=hours)
        since_str = since.isoformat()
        
        # Get recent errors with context
        errors_sql = """
        SELECT 
            timestamp,
            logger_name,
            message,
            exception_type,
            exception_message,
            extra_data
        FROM log_entries 
        WHERE level IN ('ERROR', 'CRITICAL') 
            AND timestamp > ?
        ORDER BY timestamp DESC
        LIMIT 20
        """
        
        try:
            results = db_manager.execute_query(self.db_path, errors_sql, (since_str,))
            recent_errors = []
            
            for row in results:
                error_data = {
                    'timestamp': row['timestamp'],
                    'logger': row['logger_name'],
                    'message': row['message'],
                    'exception_type': row['exception_type'],
                    'exception_message': row['exception_message']
                }
                
                # Parse extra data
                if row['extra_data']:
                    try:
                        extra = json.loads(row['extra_data'])
                        error_data['context'] = extra
                    except Exception:
                        pass
                
                recent_errors.append(error_data)
            
            return {
                'time_period': f'Last {hours} hours',
                'recent_errors': recent_errors,
                'total_errors': len(recent_errors)
            }
            
        except Exception as e:
            return {
                'error': f'Unable to fetch error analysis: {e}',
                'time_period': f'Last {hours} hours'
            }
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """Clean up old log entries"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.isoformat()
        
        try:
            # Delete old log entries
            delete_sql = "DELETE FROM log_entries WHERE timestamp < ?"
            deleted_entries = db_manager.execute_command(self.db_path, delete_sql, (cutoff_str,))
            
            # Delete old patterns (keep if recent occurrence)
            pattern_delete_sql = "DELETE FROM log_patterns WHERE last_occurrence < ?"
            deleted_patterns = db_manager.execute_command(self.db_path, pattern_delete_sql, (cutoff_str,))
            
            # Delete old aggregations
            agg_delete_sql = "DELETE FROM log_aggregations WHERE aggregation_date < ?"
            deleted_aggregations = db_manager.execute_command(self.db_path, agg_delete_sql, (cutoff_str,))
            
            return {
                'success': True,
                'deleted_entries': deleted_entries,
                'deleted_patterns': deleted_patterns,
                'deleted_aggregations': deleted_aggregations,
                'cutoff_date': cutoff_str
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Enhanced global logger instances
enhanced_auth_logger = EnhancedPowerBILogger("pbi_mcp.auth")
enhanced_powerbi_logger = EnhancedPowerBILogger("pbi_mcp.powerbi")
enhanced_mcp_logger = EnhancedPowerBILogger("pbi_mcp.server")
enhanced_monitoring_logger = EnhancedPowerBILogger("pbi_mcp.monitoring")
enhanced_database_logger = EnhancedPowerBILogger("pbi_mcp.database")
enhanced_context_logger = EnhancedPowerBILogger("pbi_mcp.context")


def get_enhanced_logger(name: str, level: str = "INFO") -> EnhancedPowerBILogger:
    """Get an enhanced logger instance for a specific component"""
    return EnhancedPowerBILogger(f"pbi_mcp.{name}", level)


# Global log analyzer instance
log_analyzer = LogAnalyzer()