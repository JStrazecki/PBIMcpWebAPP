"""
Run FastMCP server directly with HTTP transport
This creates the ASGI app internally
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("run-fastmcp")

# Import the FastMCP server
from fastmcp_server import mcp

# Get port from environment
port = int(os.environ.get('PORT', 8000))

logger.info(f"Starting FastMCP HTTP server on port {port}")
logger.info(f"Environment: {'Azure' if os.environ.get('WEBSITE_HOSTNAME') else 'Local'}")

# Run the server with HTTP transport
# This creates an internal Starlette app
mcp.run(
    transport="http",
    host="0.0.0.0",
    port=port,
    path="/mcp",
    log_level="info"
)