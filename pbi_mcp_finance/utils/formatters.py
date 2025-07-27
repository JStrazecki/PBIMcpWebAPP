"""
Data formatting utilities for Power BI MCP Finance Server
"""

from typing import Union, Any


def format_financial_number(value: Union[str, int, float], 
                          metric_type: str = "currency") -> str:
    """Format numbers for financial display"""
    try:
        num_value = float(value)
        if metric_type == "currency":
            return f"€{num_value:,.2f}"
        elif metric_type == "percentage":
            return f"{num_value:.1%}"
        elif metric_type == "count":
            return f"{num_value:,.0f}"
        else:
            return f"{num_value:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def format_measure_description(measure_info: dict) -> str:
    """Format measure description for display"""
    description = measure_info.get("description", "")
    measure_type = measure_info.get("type", "")
    statement = measure_info.get("statement", "")
    
    parts = [description]
    
    if statement:
        parts.append(f"({statement} statement)")
    
    if measure_type:
        parts.append(f"[{measure_type}]")
    
    return " ".join(parts)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def format_duration_ms(milliseconds: float) -> str:
    """Format duration in milliseconds to human readable format"""
    if milliseconds < 1000:
        return f"{milliseconds:.0f}ms"
    elif milliseconds < 60000:
        return f"{milliseconds/1000:.1f}s"
    else:
        return f"{milliseconds/60000:.1f}m"


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.1f}MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.1f}GB"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    import re
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Trim whitespace and dots
    sanitized = sanitized.strip('. ')
    return sanitized[:255]  # Limit length