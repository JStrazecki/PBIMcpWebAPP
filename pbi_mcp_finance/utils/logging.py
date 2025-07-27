"""
Logging configuration for Power BI MCP Finance Server
"""

import logging
import sys
from typing import Optional
from pathlib import Path


class PowerBILogger:
    """Centralized logging configuration"""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self._setup_logger(level)
    
    def _setup_logger(self, level: str):
        """Setup logger with console and file handlers"""
        if self.logger.handlers:
            return  # Logger already configured
        
        # Set level
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (optional)
        log_dir = Path(__file__).parent.parent.parent / "logs"
        if log_dir.exists() or self._try_create_log_dir(log_dir):
            file_handler = logging.FileHandler(log_dir / "pbi_mcp_finance.log")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _try_create_log_dir(self, log_dir: Path) -> bool:
        """Try to create log directory"""
        try:
            log_dir.mkdir(exist_ok=True)
            return True
        except Exception:
            return False
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self.logger.critical(message, **kwargs)


# Global logger instances
auth_logger = PowerBILogger("pbi_mcp.auth")
powerbi_logger = PowerBILogger("pbi_mcp.powerbi")
mcp_logger = PowerBILogger("pbi_mcp.server")
monitoring_logger = PowerBILogger("pbi_mcp.monitoring")
database_logger = PowerBILogger("pbi_mcp.database")


def get_logger(name: str, level: str = "INFO") -> PowerBILogger:
    """Get a logger instance for a specific component"""
    return PowerBILogger(f"pbi_mcp.{name}", level)