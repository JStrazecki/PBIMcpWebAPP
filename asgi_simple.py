"""
Simple ASGI wrapper for FastMCP deployment
"""

import os
import sys
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("asgi-simple")

# Import FastMCP server
from mcp_fastmcp_simple import mcp

# Get ASGI app
app = mcp.get_asgi_app(transport="http")

logger.info("Simple FastMCP ASGI app ready")