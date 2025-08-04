"""
ASGI app wrapper for Azure deployment
Creates the ASGI application for Gunicorn
"""

import os
import logging
from server import mcp

# Configure logging for Azure
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create ASGI application
app = mcp.http_app

# For debugging
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)