"""
Database connection utilities for Power BI MCP Finance Server
"""

import sqlite3
import threading
from contextlib import contextmanager
from typing import Generator, Optional, Any, Dict, List
from pathlib import Path

from ..config.settings import settings
from ..utils.logging import database_logger
from ..utils.exceptions import DatabaseConnectionError


class DatabaseManager:
    """Thread-safe SQLite database connection manager"""
    
    def __init__(self):
        self._connections = threading.local()
        self._lock = threading.Lock()
    
    def _get_connection(self, db_path: Path) -> sqlite3.Connection:
        """Get thread-local database connection"""
        db_key = str(db_path)
        
        if not hasattr(self._connections, db_key):
            try:
                conn = sqlite3.connect(
                    str(db_path),
                    check_same_thread=False,
                    timeout=30.0
                )
                conn.row_factory = sqlite3.Row  # Enable column access by name
                setattr(self._connections, db_key, conn)
                database_logger.debug(f"Created new connection to {db_path}")
            except Exception as e:
                database_logger.error(f"Failed to connect to {db_path}: {e}")
                raise DatabaseConnectionError(f"Cannot connect to database: {e}")
        
        return getattr(self._connections, db_key)
    
    @contextmanager
    def get_connection(self, db_path: Path) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection with automatic cleanup"""
        conn = None
        try:
            conn = self._get_connection(db_path)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            database_logger.error(f"Database operation failed: {e}")
            raise
    
    def execute_query(self, db_path: Path, query: str, 
                     params: Optional[tuple] = None) -> List[sqlite3.Row]:
        """Execute SELECT query and return results"""
        with self.get_connection(db_path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                database_logger.debug(f"Query returned {len(results)} rows")
                return results
            except Exception as e:
                database_logger.error(f"Query execution failed: {e}")
                raise DatabaseConnectionError(f"Query failed: {e}")
    
    def execute_command(self, db_path: Path, command: str, 
                       params: Optional[tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE command"""
        with self.get_connection(db_path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(command, params or ())
                conn.commit()
                affected_rows = cursor.rowcount
                database_logger.debug(f"Command affected {affected_rows} rows")
                return affected_rows
            except Exception as e:
                database_logger.error(f"Command execution failed: {e}")
                raise DatabaseConnectionError(f"Command failed: {e}")
    
    def execute_script(self, db_path: Path, script: str) -> int:
        """Execute multiple SQL statements (DDL script)"""
        with self.get_connection(db_path) as conn:
            try:
                cursor = conn.cursor()
                cursor.executescript(script)
                conn.commit()
                database_logger.debug("Script executed successfully")
                return 0  # executescript doesn't return rowcount
            except Exception as e:
                database_logger.error(f"Script execution failed: {e}")
                raise DatabaseConnectionError(f"Script failed: {e}")
    
    def execute_many(self, db_path: Path, command: str, 
                    params_list: List[tuple]) -> int:
        """Execute command with multiple parameter sets"""
        with self.get_connection(db_path) as conn:
            try:
                cursor = conn.cursor()
                cursor.executemany(command, params_list)
                conn.commit()
                affected_rows = cursor.rowcount
                database_logger.debug(f"Batch command affected {affected_rows} rows")
                return affected_rows
            except Exception as e:
                database_logger.error(f"Batch command execution failed: {e}")
                raise DatabaseConnectionError(f"Batch command failed: {e}")
    
    def table_exists(self, db_path: Path, table_name: str) -> bool:
        """Check if table exists in database"""
        query = """
            SELECT COUNT(*) 
            FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        try:
            results = self.execute_query(db_path, query, (table_name,))
            return results[0][0] > 0
        except Exception:
            return False
    
    def get_table_info(self, db_path: Path, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        query = f"PRAGMA table_info({table_name})"
        try:
            results = self.execute_query(db_path, query)
            return [dict(row) for row in results]
        except Exception as e:
            database_logger.error(f"Failed to get table info for {table_name}: {e}")
            return []
    
    def close_connections(self):
        """Close all thread-local connections"""
        with self._lock:
            if hasattr(self._connections, '__dict__'):
                for conn in self._connections.__dict__.values():
                    try:
                        conn.close()
                    except Exception:
                        pass
                self._connections.__dict__.clear()
                database_logger.debug("Closed all database connections")


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for specific databases
@contextmanager
def get_conversation_db() -> Generator[sqlite3.Connection, None, None]:
    """Get conversation database connection"""
    with db_manager.get_connection(settings.conversation_db_path) as conn:
        yield conn


@contextmanager
def get_metrics_db() -> Generator[sqlite3.Connection, None, None]:
    """Get metrics database connection"""
    with db_manager.get_connection(settings.metrics_db_path) as conn:
        yield conn


@contextmanager
def get_optimization_db() -> Generator[sqlite3.Connection, None, None]:
    """Get optimization database connection"""  
    with db_manager.get_connection(settings.optimization_db_path) as conn:
        yield conn