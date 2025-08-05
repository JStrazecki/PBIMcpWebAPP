"""
ASGI entry point for Azure deployment.
Since FastMCP doesn't expose an ASGI app, we create a simple redirect.
"""

import os

# Create a simple ASGI app that redirects or provides info
async def app(scope, receive, send):
    if scope["type"] == "http":
        # Get the path
        path = scope.get("path", "/")
        
        # For the root path, return a simple message
        if path == "/":
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"application/json"]],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"error": "This server requires direct FastMCP execution. Please update Azure startup command to: python run_fastmcp.py"}',
            })
        else:
            await send({
                "type": "http.response.start",
                "status": 404,
                "headers": [[b"content-type", b"text/plain"]],
            })
            await send({
                "type": "http.response.body",
                "body": b"Not Found",
            })

# Log that we need a different startup command
print("=" * 80)
print("IMPORTANT: FastMCP cannot run with gunicorn!")
print("Please update Azure App Service startup command to: python run_fastmcp.py")
print("Or use the Procfile which has the correct command.")
print("=" * 80)