# Power BI MCP Servers for Claude AI

Two clean MCP servers for Claude AI integration:

## 🔐 Server 1: Authenticated (mcp_auth_server.py)
**Requires Microsoft OAuth login**
- Users input Microsoft credentials to access
- Proper OAuth flow with state validation
- Session-based authentication
- Port: 8000

### Setup:
```bash
# Set environment variables
set AZURE_CLIENT_ID=your-client-id
set AZURE_CLIENT_SECRET=your-client-secret
set AZURE_TENANT_ID=your-tenant-id

# Start server
gunicorn --bind=0.0.0.0:8000 --workers 1 --timeout 600 --access-logfile - --error-logfile - --log-level info mcp_auth_server:app
```

### Claude Configuration:
- URL: `http://localhost:8000`
- Authentication: OAuth2
- Users will be redirected to Microsoft login

## 🔓 Server 2: Simple (mcp_simple_server.py)
**No authentication required**
- Direct connection to MCP server
- Works immediately without login
- Demo data provided
- Port: 8001

### Setup:
```bash
# Start server (no env vars needed)
gunicorn --bind=0.0.0.0:8001 --workers 1 --timeout 600 --access-logfile - --error-logfile - --log-level info mcp_simple_server:app
```

### Claude Configuration:
- URL: `http://localhost:8001`
- Authentication: None
- Visit `http://localhost:8001/claude-config` for setup help

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Choose your server:**
   - **Authenticated:** Follow Server 1 setup above
   - **Simple:** Follow Server 2 setup above

3. **Connect to Claude:**
   - Open Claude AI Settings > Connectors
   - Add Remote MCP Server
   - Use the appropriate URL and authentication setting

## 📁 Files

- `mcp_auth_server.py` - Authenticated MCP server with Microsoft OAuth
- `mcp_simple_server.py` - Simple MCP server without authentication
- `startup.txt` - Startup commands for both servers
- `requirements.txt` - Python dependencies

## 🔧 Available Endpoints

Both servers provide:
- `/` - Server information
- `/health` - Health check
- `/workspaces` - List Power BI workspaces (demo data)
- `/datasets` - Get Power BI datasets (demo data)
- `/query` - Execute Power BI queries (demo data)

Authenticated server also has:
- `/auth` - Microsoft OAuth login
- `/callback` - OAuth callback
- `/logout` - Logout

## 🌐 Azure Deployment

Use `$PORT` environment variable and increase workers:

```bash
# Authenticated server
gunicorn --bind=0.0.0.0:$PORT --workers 2 --timeout 600 --access-logfile - --error-logfile - --log-level info mcp_auth_server:app

# Simple server  
gunicorn --bind=0.0.0.0:$PORT --workers 2 --timeout 600 --access-logfile - --error-logfile - --log-level info mcp_simple_server:app
```