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

try:
    # Import the app directly (it's already created in the module)
    from mcp_fastmcp_simple import app
    logger.info("Successfully imported FastMCP ASGI app")
    logger.info(f"Running in: {'Azure' if os.environ.get('WEBSITE_HOSTNAME') else 'Local'}")
except ImportError as e:
    logger.error(f"Failed to import FastMCP app: {e}")
    # Fallback - try to create it
    try:
        from mcp_fastmcp_simple import mcp
        app = mcp.get_asgi_app(transport="http")
        logger.info("Created FastMCP ASGI app from mcp instance")
    except Exception as e2:
        logger.error(f"Failed to create app from mcp: {e2}")
        raise

logger.info("Simple FastMCP ASGI app ready for gunicorn")