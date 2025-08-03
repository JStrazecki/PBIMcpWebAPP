"""
ASGI wrapper for FastMCP to work with gunicorn
This allows FastMCP to run on Azure App Service with HTTP transport
"""

import os
import sys
import logging
from mcp_fastmcp_server import mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("pbi-asgi")

# Set transport for Azure
os.environ['MCP_TRANSPORT'] = 'http'

# Get the ASGI app from FastMCP with HTTP transport configuration
app = mcp.get_asgi_app(
    transport="http",
    path="/mcp"
)

logger.info("FastMCP ASGI app configured for Azure deployment")

# This is what gunicorn will look for
application = app