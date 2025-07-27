"""
Performance metrics and monitoring
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional

from ..database.connection import get_metrics_db
from ..config.settings import settings
from ..utils.logging import monitoring_logger


class PerformanceMonitor:
    """Enhanced monitoring for self-improving system"""
    
    def __init__(self):
        self.init_metrics_db()
        self.session_start = datetime.now()
        self.api_call_count = 0
        self.tool_call_count = 0
        self.estimated_tokens_total = 0
    
    def init_metrics_db(self):
        """Initialize enhanced metrics database"""
        try:
            with get_metrics_db() as conn:
                cursor = conn.cursor()
                
                # API metrics with detailed tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        conversation_id TEXT,
                        endpoint TEXT,
                        method TEXT,
                        status_code INTEGER,
                        response_time_ms REAL,
                        response_size INTEGER,
                        error_message TEXT,
                        request_payload TEXT,
                        dax_query TEXT
                    )
                """)
                
                # Tool metrics with pattern tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tool_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        conversation_id TEXT,
                        tool_name TEXT,
                        execution_time_ms REAL,
                        success BOOLEAN,
                        estimated_tokens INTEGER,
                        input_params TEXT,
                        output_preview TEXT,
                        error_message TEXT,
                        dax_query TEXT,
                        retry_count INTEGER DEFAULT 0,
                        technical_success BOOLEAN,
                        quality_success BOOLEAN,
                        quality_score REAL,
                        quality_issues TEXT
                    )
                """)
                
                # Failed queries for learning
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS failed_queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        conversation_id TEXT,
                        tool_name TEXT,
                        query_type TEXT,
                        error_message TEXT,
                        full_error TEXT,
                        user_question TEXT,
                        attempted_dax TEXT,
                        suggested_fix TEXT
                    )
                """)
                
                # Token usage tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS token_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        conversation_id TEXT,
                        tool_name TEXT,
                        input_tokens INTEGER,
                        output_tokens INTEGER,
                        total_tokens INTEGER,
                        cost_estimate REAL
                    )
                """)
                
                # Tool confusion matrix
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tool_confusion (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        intended_action TEXT,
                        wrong_tool_selected TEXT,
                        correct_tool TEXT,
                        user_query TEXT,
                        frequency INTEGER DEFAULT 1
                    )
                """)
                
                conn.commit()
                monitoring_logger.info(f"Metrics DB initialized at: {settings.metrics_db_path}")
        except Exception as e:
            monitoring_logger.error(f"Error initializing metrics DB: {e}")
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token)"""
        if not text:
            return 0
        return len(str(text)) // 4
    
    def log_api_call(self, endpoint: str, method: str, status_code: int, response_time_ms: float,
                     response_size: int = 0, error_message: Optional[str] = None, 
                     request_payload: Optional[Dict] = None, dax_query: Optional[str] = None,
                     conversation_id: Optional[str] = None) -> None:
        """Log API call with conversation context"""
        try:
            with get_metrics_db() as conn:
                conn.execute("""
                    INSERT INTO api_metrics 
                    (conversation_id, endpoint, method, status_code, response_time_ms, 
                     response_size, error_message, request_payload, dax_query)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conversation_id,
                    endpoint, method, status_code, response_time_ms, 
                    response_size, error_message, 
                    json.dumps(request_payload) if request_payload else None,
                    dax_query
                ))
                conn.commit()
                self.api_call_count += 1
                monitoring_logger.debug(f"Logged API call: {method} {endpoint} ({status_code})")
        except Exception as e:
            monitoring_logger.error(f"Error logging API call: {e}")
    
    def log_tool_execution(self, tool_name: str, execution_time_ms: float, success: bool, 
                          input_params: Optional[Dict] = None, output_preview: Optional[str] = None,
                          error_message: Optional[str] = None, dax_query: Optional[str] = None,
                          retry_count: int = 0, conversation_id: Optional[str] = None,
                          technical_success: Optional[bool] = None, quality_success: Optional[bool] = None,
                          quality_score: Optional[float] = None, quality_issues: Optional[list] = None) -> None:
        """Log tool execution with enhanced details"""
        try:
            # Estimate tokens
            input_tokens = self.estimate_tokens(json.dumps(input_params) if input_params else "")
            output_tokens = self.estimate_tokens(output_preview)
            total_tokens = input_tokens + output_tokens
            self.estimated_tokens_total += total_tokens
            
            with get_metrics_db() as conn:
                conn.execute("""
                    INSERT INTO tool_metrics 
                    (conversation_id, tool_name, execution_time_ms, success, estimated_tokens, 
                     input_params, output_preview, error_message, dax_query, retry_count,
                     technical_success, quality_success, quality_score, quality_issues)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conversation_id,
                    tool_name, execution_time_ms, success, total_tokens,
                    json.dumps(input_params) if input_params else None,
                    output_preview[:500] if output_preview else None,
                    error_message, dax_query, retry_count,
                    technical_success if technical_success is not None else success,
                    quality_success if quality_success is not None else success,
                    quality_score if quality_score is not None else 1.0,
                    json.dumps(quality_issues) if quality_issues else None
                ))
                
                # Also log token usage
                conn.execute("""
                    INSERT INTO token_usage 
                    (conversation_id, tool_name, input_tokens, output_tokens, total_tokens, cost_estimate)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    conversation_id,
                    tool_name, input_tokens, output_tokens, total_tokens, 
                    total_tokens * 0.00002  # Rough cost estimate
                ))
                
                conn.commit()
                self.tool_call_count += 1
                monitoring_logger.debug(f"Logged tool execution: {tool_name} ({execution_time_ms:.1f}ms)")
                
        except Exception as e:
            monitoring_logger.error(f"Error logging tool execution: {e}")
    
    def log_tool_confusion(self, intended_action: str, wrong_tool: str, correct_tool: str, 
                          user_query: str) -> None:
        """Log when wrong tool is selected"""
        try:
            with get_metrics_db() as conn:
                # Check if this confusion pattern exists
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, frequency FROM tool_confusion
                    WHERE intended_action = ? AND wrong_tool_selected = ? AND correct_tool = ?
                """, (intended_action, wrong_tool, correct_tool))
                
                existing = cursor.fetchone()
                if existing:
                    # Update frequency
                    conn.execute("""
                        UPDATE tool_confusion SET frequency = frequency + 1 
                        WHERE id = ?
                    """, (existing[0],))
                else:
                    # Insert new confusion pattern
                    conn.execute("""
                        INSERT INTO tool_confusion 
                        (intended_action, wrong_tool_selected, correct_tool, user_query)
                        VALUES (?, ?, ?, ?)
                    """, (intended_action, wrong_tool, correct_tool, user_query))
                
                conn.commit()
                monitoring_logger.debug(f"Logged tool confusion: {wrong_tool} -> {correct_tool}")
        except Exception as e:
            monitoring_logger.error(f"Error logging tool confusion: {e}")


# Global monitor instance
performance_monitor = PerformanceMonitor()