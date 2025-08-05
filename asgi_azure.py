"""
ASGI entry point for Azure deployment with gunicorn
This wraps the FastMCP + Flask combined application
"""

import os
import sys
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("asgi-azure")

# Import and get the application
try:
    from mcp_fastmcp_azure import application
    logger.info("Successfully imported FastMCP + Flask application")
except Exception as e:
    logger.error(f"Failed to import application: {e}")
    raise

# Log startup information
logger.info(f"ASGI wrapper ready for Azure deployment")
logger.info(f"Environment: {'Azure' if os.environ.get('WEBSITE_HOSTNAME') else 'Local'}")
logger.info(f"Python path: {sys.path}")

# Export for gunicorn
app = application