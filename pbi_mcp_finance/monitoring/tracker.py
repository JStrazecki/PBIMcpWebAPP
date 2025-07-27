"""
Conversation tracking and pattern analysis
"""

import json
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..database.connection import get_conversation_db
from ..config.settings import settings
from ..utils.logging import monitoring_logger


class ConversationTracker:
    """Tracks conversation flow and tool usage patterns"""
    
    def __init__(self):
        self.current_conversation_id: Optional[str] = None
        self.conversation_start: Optional[datetime] = None
        self.tool_sequence: List[Dict[str, Any]] = []
        self.user_query: Optional[str] = None
        self.init_conversation_db()
    
    def init_conversation_db(self):
        """Initialize conversation tracking database"""
        try:
            with get_conversation_db() as conn:
                cursor = conn.cursor()
                
                # Tool usage patterns table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tool_usage_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        user_query TEXT,
                        tools_attempted TEXT,
                        tool_sequence TEXT,
                        first_tool_success BOOLEAN,
                        total_attempts INTEGER,
                        response_time_ms INTEGER,
                        token_count INTEGER,
                        api_errors INTEGER,
                        final_success BOOLEAN,
                        conversation_context TEXT
                    )
                """)
                
                # Conversation flow table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_flow (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT,
                        step_number INTEGER,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        tool_name TEXT,
                        input_params TEXT,
                        execution_time_ms REAL,
                        success BOOLEAN,
                        error_message TEXT,
                        output_preview TEXT,
                        tokens_used INTEGER
                    )
                """)
                
                # Query patterns table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS query_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_hash TEXT,
                        query_text TEXT,
                        successful_tool TEXT,
                        avg_attempts REAL,
                        success_rate REAL,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                monitoring_logger.info(f"Conversation DB initialized at: {settings.conversation_db_path}")
        except Exception as e:
            monitoring_logger.error(f"Error initializing conversation DB: {e}")
    
    def start_conversation(self, user_query: str) -> str:
        """Start tracking a new conversation"""
        self.current_conversation_id = str(uuid.uuid4())
        self.conversation_start = datetime.now()
        self.tool_sequence = []
        self.user_query = user_query
        
        monitoring_logger.info(f"Started conversation {self.current_conversation_id}")
        monitoring_logger.debug(f"User query: {user_query[:100]}...")
        
        return self.current_conversation_id
    
    def add_tool_execution(self, tool_name: str, success: bool, execution_time_ms: float,
                          input_params: Optional[Dict] = None, error_msg: Optional[str] = None,
                          output_preview: Optional[str] = None) -> None:
        """Add a tool execution to the current conversation"""
        if not self.current_conversation_id:
            # Auto-start conversation if not started
            query = "Tool execution: " + tool_name
            if input_params and isinstance(input_params, dict):
                query = input_params.get('query', query)
            self.start_conversation(query)
        
        self.tool_sequence.append({
            'tool': tool_name,
            'success': success,
            'time': execution_time_ms
        })
        
        try:
            with get_conversation_db() as conn:
                conn.execute("""
                    INSERT INTO conversation_flow 
                    (conversation_id, step_number, tool_name, input_params, execution_time_ms, 
                     success, error_message, output_preview, tokens_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.current_conversation_id,
                    len(self.tool_sequence),
                    tool_name,
                    json.dumps(input_params) if input_params else None,
                    execution_time_ms,
                    success,
                    error_msg,
                    output_preview[:500] if output_preview else None,
                    len(str(input_params) + str(output_preview)) // 4 if output_preview else 0
                ))
                conn.commit()
                
            monitoring_logger.debug(f"Added tool execution: {tool_name} (success={success})")
            
            # Auto-save conversation after each tool execution for MCP stateless nature
            self._auto_save_conversation(success)
            
        except Exception as e:
            monitoring_logger.error(f"Error logging tool execution: {e}")
    
    def _auto_save_conversation(self, current_success: bool = True) -> None:
        """Auto-save conversation data after each tool execution (for MCP stateless nature)"""
        if not self.current_conversation_id:
            return
        
        try:
            # Calculate metrics
            total_time = (datetime.now() - self.conversation_start).total_seconds() * 1000
            total_attempts = len(self.tool_sequence)
            first_tool_success = self.tool_sequence[0]['success'] if self.tool_sequence else False
            api_errors = sum(1 for t in self.tool_sequence if not t['success'])
            
            with get_conversation_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM tool_usage_patterns 
                    WHERE conversation_id = ?
                """, (self.current_conversation_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing conversation
                    conn.execute("""
                        UPDATE tool_usage_patterns
                        SET tools_attempted = ?,
                            tool_sequence = ?,
                            total_attempts = ?,
                            response_time_ms = ?,
                            api_errors = ?,
                            final_success = ?
                        WHERE conversation_id = ?
                    """, (
                        json.dumps([t['tool'] for t in self.tool_sequence]),
                        json.dumps(self.tool_sequence),
                        total_attempts,
                        int(total_time),
                        api_errors,
                        current_success,
                        self.current_conversation_id
                    ))
                else:
                    # Insert new conversation
                    conn.execute("""
                        INSERT INTO tool_usage_patterns
                        (conversation_id, user_query, tools_attempted, tool_sequence, 
                         first_tool_success, total_attempts, response_time_ms, 
                         api_errors, final_success)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.current_conversation_id,
                        self.user_query,
                        json.dumps([t['tool'] for t in self.tool_sequence]),
                        json.dumps(self.tool_sequence),
                        first_tool_success,
                        total_attempts,
                        int(total_time),
                        api_errors,
                        current_success
                    ))
                
                conn.commit()
                monitoring_logger.debug(f"Auto-saved conversation state: {total_attempts} tools, {total_time:.0f}ms")
                
        except Exception as e:
            monitoring_logger.error(f"Error auto-saving conversation: {e}")
    
    def end_conversation(self, final_success: bool = True) -> None:
        """End conversation and save pattern analysis"""
        if not self.current_conversation_id:
            return
        
        try:
            # Calculate metrics
            total_time = (datetime.now() - self.conversation_start).total_seconds() * 1000
            total_attempts = len(self.tool_sequence)
            first_tool_success = self.tool_sequence[0]['success'] if self.tool_sequence else False
            api_errors = sum(1 for t in self.tool_sequence if not t['success'])
            
            # Save conversation pattern
            with get_conversation_db() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO tool_usage_patterns
                    (conversation_id, user_query, tools_attempted, tool_sequence, 
                     first_tool_success, total_attempts, response_time_ms, 
                     api_errors, final_success)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.current_conversation_id,
                    self.user_query,
                    json.dumps([t['tool'] for t in self.tool_sequence]),
                    json.dumps(self.tool_sequence),
                    first_tool_success,
                    total_attempts,
                    int(total_time),
                    api_errors,
                    final_success
                ))
                
                # Update query pattern statistics
                if self.user_query:
                    query_hash = hashlib.md5(self.user_query.lower().encode()).hexdigest()
                    successful_tool = next((t['tool'] for t in self.tool_sequence if t['success']), None)
                    
                    if successful_tool:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT id, avg_attempts, success_rate FROM query_patterns 
                            WHERE query_hash = ?
                        """, (query_hash,))
                        
                        existing = cursor.fetchone()
                        if existing:
                            # Update existing pattern
                            new_avg_attempts = (existing[1] + total_attempts) / 2
                            new_success_rate = (existing[2] + (1 if final_success else 0)) / 2
                            
                            conn.execute("""
                                UPDATE query_patterns 
                                SET avg_attempts = ?, success_rate = ?, last_updated = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (new_avg_attempts, new_success_rate, existing[0]))
                        else:
                            # Create new pattern
                            conn.execute("""
                                INSERT INTO query_patterns 
                                (query_hash, query_text, successful_tool, avg_attempts, success_rate)
                                VALUES (?, ?, ?, ?, ?)
                            """, (query_hash, self.user_query, successful_tool, total_attempts, 1 if final_success else 0))
                
                conn.commit()
                
            monitoring_logger.info(f"Ended conversation {self.current_conversation_id}: {total_attempts} attempts, {total_time:.0f}ms")
            
        except Exception as e:
            monitoring_logger.error(f"Error ending conversation: {e}")
        finally:
            # Reset for next conversation
            self.current_conversation_id = None
            self.conversation_start = None
            self.tool_sequence = []
            self.user_query = None


# Global conversation tracker
conversation_tracker = ConversationTracker()


def log_conversation_simple(tool_name: str, kwargs: Dict[str, Any], success: bool = True, error: Optional[str] = None) -> bool:
    """Simple direct conversation logging for MCP tools"""
    try:
        conv_id = f"mcp-{datetime.now().strftime('%Y%m%d%H%M%S%f')}-{tool_name}"
        user_query = "Tool execution"
        
        if isinstance(kwargs, dict):
            user_query = kwargs.get('query', kwargs.get('measure_name', 
                        kwargs.get('breakdown_by', kwargs.get('period', f"Tool: {tool_name}"))))
        
        monitoring_logger.debug(f"Logging conversation: {tool_name}")
        
        with get_conversation_db() as conn:
            # Log to conversation_flow
            conn.execute("""
                INSERT INTO conversation_flow 
                (conversation_id, step_number, tool_name, input_params, execution_time_ms, 
                 success, error_message, output_preview, tokens_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conv_id,
                1,
                tool_name,
                json.dumps(kwargs) if kwargs else "{}",
                100,  # Default time
                success,
                str(error) if error else None,
                "Tool executed",
                10
            ))
            
            # Log to tool_usage_patterns
            conn.execute("""
                INSERT INTO tool_usage_patterns
                (conversation_id, user_query, tools_attempted, tool_sequence, 
                 first_tool_success, total_attempts, response_time_ms, 
                 api_errors, final_success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conv_id,
                str(user_query),
                json.dumps([tool_name]),
                json.dumps([{'tool': tool_name, 'success': success, 'time': 100}]),
                success,
                1,
                100,
                0 if success else 1,
                success
            ))
            
            conn.commit()
            monitoring_logger.debug(f"Successfully logged {tool_name} to conversation DB")
            return True
    except Exception as e:
        monitoring_logger.error(f"Error logging conversation: {e}")
        return False