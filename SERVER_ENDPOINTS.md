# MCP Server Endpoints Documentation

## Overview
This document lists all available endpoints in the Power BI MCP Server (`mcp_simple_server.py`).

## Base URL
- Local: `http://localhost:8000`
- Azure: `https://pbimcp.azurewebsites.net`

## Authentication
- OAuth2 flow for Claude.ai integration
- Bearer token required for MCP protocol endpoints
- Client credentials validation using Power BI app registration

## Endpoints

### 1. Root Endpoint
**Route:** `/`  
**Methods:** `GET`, `POST`  
**Description:** MCP Server root endpoint - handles both server info and HTTP transport for MCP protocol

#### GET Request
- Returns server information if not SSE request
- Handles SSE transport if `Accept: text/event-stream` header present

#### POST Request
- Handles JSON-RPC 2.0 requests for MCP protocol
- Supported methods:
  - `initialize`
  - `notifications/initialized`
  - `initialized`
  - `tools/list`
  - `tools/call`

### 2. MCP Discovery
**Route:** `/.well-known/mcp`  
**Methods:** `GET`  
**Description:** MCP discovery endpoint that advertises server capabilities and transport options

**Response:**
```json
{
  "version": "2024-11-05",
  "transport": {
    "type": "http",
    "http_url": "{base_url}/",
    "sse_url": "{base_url}/sse",
    "message_url": "{base_url}/message"
  },
  "authentication": {
    "type": "oauth2",
    "authorization_url": "{base_url}/authorize",
    "token_url": "{base_url}/token",
    "scopes": ["powerbi"]
  },
  "capabilities": {
    "tools": true,
    "resources": false,
    "prompts": false,
    "logging": true
  }
}
```

### 3. Health Check
**Route:** `/health`  
**Methods:** `GET`  
**Description:** Health check endpoint that verifies server status and Power BI configuration

**Response Example:**
```json
{
  "status": "healthy",
  "service": "Power BI MCP Server (Simple)",
  "version": "2.2.0-simplified",
  "authentication": "client_credentials",
  "powerbi_configured": true,
  "powerbi_access": "granted",
  "client_id_configured": true,
  "environment": "Azure",
  "mcp_endpoints_added": true,
  "timestamp": "2025-08-03T14:00:00Z"
}
```

### 4. OAuth2 Authorization
**Route:** `/authorize`  
**Methods:** `GET`, `POST`  
**Description:** OAuth2 authorization endpoint for Claude.ai authentication flow

**Parameters:**
- `client_id`: OAuth client ID
- `redirect_uri`: Callback URL (defaults to `https://claude.ai/api/mcp/auth_callback`)
- `state`: OAuth state parameter
- `code_challenge`: PKCE code challenge (optional)

**Response:** Redirects to callback URL with authorization code

### 5. OAuth2 Token
**Route:** `/token`  
**Methods:** `POST`  
**Description:** OAuth2 token endpoint that validates client credentials and issues access tokens

**Request Body (form-data):**
- `grant_type`: Must be `authorization_code`
- `code`: Authorization code from authorize endpoint
- `client_id`: OAuth client ID
- `client_secret`: OAuth client secret
- `redirect_uri`: Same as used in authorize
- `code_verifier`: PKCE code verifier (optional)

**Response:**
```json
{
  "access_token": "{token}",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "powerbi"
}
```

### 6. SSE Transport
**Route:** `/sse`  
**Methods:** `GET`  
**Description:** Server-Sent Events endpoint for real-time MCP communication

**Headers Required:**
- `Authorization: Bearer {token}`

**Event Stream:**
- Initial `connection` event with protocol version
- Periodic `heartbeat` events every 15 seconds
- No tools sent via SSE (Claude must request via tools/list)

### 7. Message Endpoint
**Route:** `/message`  
**Methods:** `POST`  
**Description:** Alternative message endpoint for MCP protocol communication

**Supported Methods:**
- `initialize`
- `notifications/initialized`
- `tools/list`
- `tools/call`

### 8. Power BI Workspaces
**Route:** `/workspaces`  
**Methods:** `GET`  
**Description:** List Power BI workspaces (real data if configured, demo otherwise)

**Response:**
```json
{
  "workspaces": [
    {
      "id": "workspace-id",
      "name": "Workspace Name",
      "type": "Workspace",
      "state": "Active",
      "is_read_only": false,
      "is_on_dedicated_capacity": false
    }
  ],
  "total_count": 3,
  "mode": "real_powerbi_data",
  "authentication": "client_credentials",
  "timestamp": "2025-08-03T14:00:00Z"
}
```

### 9. Power BI Datasets
**Route:** `/datasets`  
**Methods:** `GET`  
**Description:** Get Power BI datasets from workspaces

**Query Parameters:**
- `workspace_id` (optional): Filter datasets by workspace

**Response:**
```json
{
  "workspace_id": "workspace-id",
  "datasets": [
    {
      "id": "dataset-id",
      "name": "Dataset Name",
      "web_url": "https://...",
      "configured_by": "user@example.com",
      "is_refreshable": true,
      "created_date": "2025-01-01T00:00:00Z",
      "content_provider_type": "PBI"
    }
  ],
  "total_count": 5,
  "mode": "real_powerbi_data",
  "timestamp": "2025-08-03T14:00:00Z"
}
```

### 10. Power BI Query
**Route:** `/query`  
**Methods:** `POST`  
**Description:** Execute DAX queries against Power BI datasets

**Request Body:**
```json
{
  "dataset_id": "dataset-id",
  "dax_query": "EVALUATE VALUES(Table[Column])",
  "workspace_id": "workspace-id" // optional
}
```

**Response:**
```json
{
  "dataset_id": "dataset-id",
  "workspace_id": "workspace-id",
  "dax_query": "EVALUATE VALUES(Table[Column])",
  "results": [...],
  "mode": "real_powerbi_query",
  "execution_time": "2025-08-03T14:00:00Z",
  "status": "success"
}
```

### 11. Claude Configuration Helper
**Route:** `/claude-config`  
**Methods:** `GET`  
**Description:** Provides configuration instructions for setting up the server in Claude.ai

### 12. Test Endpoints

#### Test Deployment
**Route:** `/test-deployment`  
**Methods:** `GET`  
**Description:** Verify deployment and list available endpoints

#### Test POST
**Route:** `/test-post`  
**Methods:** `POST`  
**Description:** Simple test endpoint for POST requests

### 13. Direct MCP Protocol Endpoints

#### MCP Initialize
**Route:** `/mcp/initialize`  
**Methods:** `POST`  
**Description:** Direct MCP protocol initialize endpoint

#### MCP Tools List
**Route:** `/mcp/tools/list`  
**Methods:** `POST`  
**Description:** Direct MCP protocol endpoint to list available tools

#### MCP Tools Call
**Route:** `/mcp/tools/call`  
**Methods:** `POST`  
**Description:** Direct MCP protocol endpoint to execute tool calls

### 14. CORS Preflight Handlers
**Routes:** Multiple endpoints  
**Methods:** `OPTIONS`  
**Description:** Handle CORS preflight requests for all endpoints

## Available MCP Tools

### 1. powerbi_health
Check Power BI server health and configuration status

### 2. powerbi_workspaces
List Power BI workspaces accessible to the server

### 3. powerbi_datasets
Get Power BI datasets from a specific workspace or all accessible workspaces
- Parameters:
  - `workspace_id` (optional)

### 4. powerbi_query
Execute a DAX query against a Power BI dataset
- Parameters:
  - `dataset_id` (required)
  - `dax_query` (required)
  - `workspace_id` (optional)

## Response Formats

All MCP protocol responses follow JSON-RPC 2.0 format:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {...}
}
```

Error responses:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found"
  }
}
```

## Authentication Flow

1. Claude.ai initiates OAuth flow by calling `/authorize`
2. Server redirects to Claude's callback URL with authorization code
3. Claude exchanges code for access token via `/token` endpoint
4. Access token is used as Bearer token for subsequent MCP requests

## Notes

- SSE connections send heartbeats every 15 seconds to maintain connection
- Tools are not sent automatically - Claude must request them via `tools/list`
- Demo data is provided when Power BI credentials are not configured
- All endpoints support CORS for Claude.ai integration