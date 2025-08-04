"""
ASGI wrapper for FastMCP to work with gunicorn
This allows FastMCP to run on Azure App Service with HTTP transport
"""

import os
import sys
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_fastmcp_server_new import mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("pbi-asgi")

# Set transport for Azure
os.environ['MCP_TRANSPORT'] = 'http'

# Get the ASGI app from FastMCP
app = mcp.http_app

logger.info("FastMCP ASGI app configured for Azure deployment")

# This is what gunicorn will look for
application = app