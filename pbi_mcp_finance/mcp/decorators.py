"""
Decorators for MCP tools with monitoring and tracking
"""

import time
from functools import wraps
from typing import Callable, Any

from ..monitoring.tracker import conversation_tracker, log_conversation_simple
from ..monitoring.metrics import performance_monitor
from ..utils.logging import mcp_logger


def enhanced_tool(func: Callable) -> Callable:
    """Enhanced decorator for comprehensive monitoring and conversation tracking"""
    @wraps(func)
    def wrapper(**kwargs):
        start_time = time.time()
        success = True
        error_message = None
        output = None
        
        # Log start of tool execution
        mcp_logger.debug(f"Starting tool: {func.__name__}")
        
        # Simple conversation logging for MCP stateless nature
        log_conversation_simple(func.__name__, kwargs, success=True)
        
        try:
            # Execute the function
            output = func(**kwargs)
            
            # Check for technical errors
            if isinstance(output, str) and output.startswith("Error:"):
                success = False
                error_message = output
            
            return output
            
        except Exception as e:
            success = False
            error_message = str(e)
            mcp_logger.error(f"Tool {func.__name__} failed: {e}")
            return f"Error: {str(e)}"
            
        finally:
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Log execution metrics
            performance_monitor.log_tool_execution(
                tool_name=func.__name__,
                execution_time_ms=elapsed_ms,
                success=success,
                input_params=kwargs,
                output_preview=str(output)[:500] if output else None,
                error_message=error_message,
                conversation_id=conversation_tracker.current_conversation_id
            )
            
            # Log to conversation tracker
            conversation_tracker.add_tool_execution(
                tool_name=func.__name__,
                success=success,
                execution_time_ms=elapsed_ms,
                input_params=kwargs,
                error_msg=error_message,
                output_preview=str(output)[:500] if output else None
            )
            
            mcp_logger.debug(f"Tool {func.__name__} completed in {elapsed_ms:.1f}ms")
    
    return wrapper