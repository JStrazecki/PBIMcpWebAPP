"""
MCP tools for monitoring and performance statistics
"""

import sqlite3
from fastmcp import FastMCP

from ...database.connection import get_conversation_db, get_metrics_db
from ...utils.logging import mcp_logger


def register_monitoring_tools(mcp: FastMCP):
    """Register monitoring and performance MCP tools"""
    
    @mcp.tool()
    def get_performance_stats() -> str:
        """
        Get comprehensive performance statistics for the current session.
        
        Shows API calls, tool executions, conversation patterns, and optimization opportunities.
        """
        try:
            mcp_logger.info("Retrieving performance statistics")
            
            with get_conversation_db() as conv_conn:
                cursor = conv_conn.cursor()
                
                # Get conversation patterns
                cursor.execute("""
                    SELECT COUNT(*) as total_conversations,
                           AVG(total_attempts) as avg_attempts,
                           AVG(CASE WHEN first_tool_success = 1 THEN 1 ELSE 0 END) as first_success_rate,
                           AVG(response_time_ms) as avg_response_time
                    FROM tool_usage_patterns
                    WHERE timestamp > datetime('now', '-24 hours')
                """)
                conv_stats = cursor.fetchone()
            
            with get_metrics_db() as metrics_conn:
                cursor = metrics_conn.cursor()
                
                # Get tool confusion patterns
                cursor.execute("""
                    SELECT wrong_tool_selected, correct_tool, COUNT(*) as frequency
                    FROM tool_confusion
                    GROUP BY wrong_tool_selected, correct_tool
                    ORDER BY frequency DESC
                    LIMIT 5
                """)
                confusions = cursor.fetchall()
            
            with get_conversation_db() as conv_conn:
                cursor = conv_conn.cursor()
                
                # Get most efficient query patterns
                cursor.execute("""
                    SELECT query_text, successful_tool, avg_attempts, success_rate
                    FROM query_patterns
                    WHERE success_rate > 0.8
                    ORDER BY avg_attempts ASC
                    LIMIT 5
                """)
                efficient_patterns = cursor.fetchall()
            
            # Format output
            output = "📊 Enhanced Performance Statistics\n"
            output += "="*60 + "\n\n"
            
            output += "📈 Conversation Analytics (24h):\n"
            output += f"• Total Conversations: {conv_stats[0] or 0}\n"
            output += f"• Avg Tool Attempts: {conv_stats[1] or 0:.1f}\n"
            output += f"• First Tool Success Rate: {(conv_stats[2] or 0) * 100:.1f}%\n"
            output += f"• Avg Response Time: {conv_stats[3] or 0:.0f}ms\n\n"
            
            output += "🔀 Tool Confusion Patterns:\n"
            if confusions:
                for wrong, correct, freq in confusions:
                    output += f"• {wrong} → {correct}: {freq} times\n"
            else:
                output += "• No confusion patterns detected\n"
            
            output += "\n✅ Most Efficient Query Patterns:\n"
            if efficient_patterns:
                for query, tool, attempts, rate in efficient_patterns[:3]:
                    query_text = query[:50] + "..." if query and len(query) > 50 else query or "Unknown"
                    output += f"• \"{query_text}\" → {tool}\n"
                    output += f"  Success: {rate*100:.0f}%, Avg attempts: {attempts:.1f}\n"
            else:
                output += "• No patterns analyzed yet\n"
            
            from ...config.settings import settings
            output += f"\n💾 Databases:\n"
            output += f"• Conversation DB: {settings.conversation_db_path}\n"
            output += f"• Metrics DB: {settings.metrics_db_path}\n"
            
            return output
            
        except Exception as e:
            mcp_logger.error(f"Failed to retrieve performance stats: {e}")
            return f"Error retrieving performance stats: {str(e)}"