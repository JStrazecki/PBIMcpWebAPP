# Power BI MCP Server - Architecture & Workflow Documentation

## 🏗️ System Architecture

### High-Level Architecture
```
┌─────────────────┐    OAuth 2.0    ┌─────────────────┐    JWT + HTTPS    ┌─────────────────┐
│  Claude.ai      │◄──────────────►│ Azure API       │◄─────────────────►│ Azure Web App   │
│  Enterprise     │                 │ Management      │                    │ (MCP Bridge)    │
└─────────────────┘                 └─────────────────┘                    └─────────────────┘
                                            │                                        │
                                            │ Security Policies                      │ Client Credentials
                                            │ - JWT Validation                       │ OAuth 2.0
                                            │ - Rate Limiting                        │
                                            │ - CORS                                 │
                                            │ - Audit Logging                        ▼
                                            │                                ┌─────────────────┐
                                            │                                │ Power BI        │
                                            │                                │ REST API        │
                                            │                                └─────────────────┘
                                            │                                        │
                                            │                                        │ Direct Access
                                            │                                        ▼
                                            │                                ┌─────────────────┐
                                            │                                │ Power BI        │
                                            └────────────── Monitoring ────►│ Workspaces &    │
                                                                            │ Datasets        │
                                                                            └─────────────────┘
```

### Component Details

#### 1. Claude.ai Enterprise Client
- **Role:** MCP client and user interface
- **Authentication:** OAuth 2.0 with Microsoft Entra ID
- **Communication:** HTTPS REST API calls
- **Features:** Natural language interface to Power BI data

#### 2. Azure API Management (Security Gateway)
- **Role:** Enterprise security and API gateway
- **Key Features:**
  - JWT token validation
  - OAuth 2.0 server configuration
  - Rate limiting and quotas
  - CORS policy enforcement
  - Request/response logging
  - Security headers injection
- **Benefits:**
  - Centralized authentication
  - Enterprise-grade security
  - API analytics and monitoring
  - Scalable architecture

#### 3. Azure Web App (MCP Bridge Server)
- **File:** `mcp_bridge.py`
- **Role:** HTTP-to-MCP protocol bridge
- **Key Features:**
  - FastMCP integration for MCP tools
  - Power BI REST API client
  - OAuth token management
  - Async operation handling
- **Endpoints:**
  - `/health` - Health check
  - `/mcp/status` - Server status
  - `/mcp/workspaces` - List workspaces
  - `/mcp/datasets` - List datasets
  - `/mcp/query` - Execute DAX queries
  - `/authorize` - OAuth initiation
  - `/auth/callback` - OAuth callback

#### 4. Power BI REST API
- **Role:** Data source integration
- **Authentication:** Client credentials OAuth 2.0
- **Capabilities:**
  - Workspace enumeration
  - Dataset discovery
  - DAX query execution
  - Real-time data access

## 🔄 Authentication Workflow

### OAuth 2.0 Flow Sequence
```
1. Claude.ai → GET /powerbi-mcp/authorize
   ┌─────────────────────────────────────────────────────────────┐
   │ Parameters:                                                 │
   │ - response_type=code                                        │
   │ - client_id=5bdb10bc-bb29-4af9-8cb5-062690e6be15          │
   │ - redirect_uri=https://claude.ai/api/mcp/auth_callback     │
   │ - scope=https://analysis.windows.net/powerbi/api/.default │
   │ - state=random_string                                       │
   └─────────────────────────────────────────────────────────────┘

2. API Management → Redirect to Microsoft OAuth
   ┌─────────────────────────────────────────────────────────────┐
   │ URL: https://login.microsoftonline.com/{tenant}/oauth2/     │
   │      v2.0/authorize?[params]                                │
   └─────────────────────────────────────────────────────────────┘

3. User → Microsoft Login & Consent

4. Microsoft → POST /powerbi-mcp/auth/callback
   ┌─────────────────────────────────────────────────────────────┐
   │ Parameters:                                                 │
   │ - code=authorization_code                                   │
   │ - state=random_string                                       │
   └─────────────────────────────────────────────────────────────┘

5. API Management → Exchange code for tokens
   ┌─────────────────────────────────────────────────────────────┐
   │ POST https://login.microsoftonline.com/{tenant}/oauth2/     │
   │      v2.0/token                                             │
   │ Body:                                                       │
   │ - grant_type=authorization_code                             │
   │ - code=authorization_code                                   │
   │ - client_id=5bdb10bc-bb29-4af9-8cb5-062690e6be15          │
   │ - client_secret=your_secret                                 │
   └─────────────────────────────────────────────────────────────┘

6. Microsoft → Returns access_token + refresh_token

7. API Management → Redirect to Claude.ai
   ┌─────────────────────────────────────────────────────────────┐
   │ URL: https://claude.ai/api/mcp/auth_callback?               │
   │      code=authorization_code&state=random_string            │
   └─────────────────────────────────────────────────────────────┘

8. Claude.ai → Stores tokens for future API calls
```

### Subsequent API Calls
```
Claude.ai → API Management
┌─────────────────────────────────────────────────────────────┐
│ Header: Authorization: Bearer {jwt_token}                   │
│ URL: https://gateway/powerbi-mcp/mcp/workspaces            │
└─────────────────────────────────────────────────────────────┘

API Management → Validates JWT
┌─────────────────────────────────────────────────────────────┐
│ 1. Verify JWT signature against Azure AD                   │
│ 2. Check token expiration                                   │
│ 3. Validate audience and scopes                             │
│ 4. Apply rate limiting                                      │
│ 5. Log request for audit                                    │
└─────────────────────────────────────────────────────────────┘

API Management → Azure Web App
┌─────────────────────────────────────────────────────────────┐
│ URL: https://pbimcp.azurewebsites.net/mcp/workspaces      │
│ Headers: X-Correlation-ID, security headers                │
└─────────────────────────────────────────────────────────────┘

Azure Web App → Power BI API
┌─────────────────────────────────────────────────────────────┐
│ URL: https://api.powerbi.com/v1.0/myorg/groups            │
│ Header: Authorization: Bearer {powerbi_token}              │
│ Method: Client credentials OAuth                            │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Data Flow Diagrams

### Power BI Workspace Discovery
```
Claude.ai User Request: "Show me available Power BI workspaces"
                          ↓
         Claude.ai processes natural language request
                          ↓
      Claude.ai → GET /powerbi-mcp/mcp/workspaces
                          ↓
           API Management validates JWT token
                          ↓
         API Management → Azure Web App endpoint
                          ↓
      Azure Web App calls list_powerbi_workspaces()
                          ↓
       Azure Web App acquires Power BI token (client creds)
                          ↓
    Azure Web App → GET https://api.powerbi.com/v1.0/myorg/groups
                          ↓
              Power BI returns workspace list
                          ↓
           Azure Web App formats response as JSON
                          ↓
         API Management adds security headers & logs
                          ↓
          Claude.ai receives formatted workspace data
                          ↓
        Claude.ai presents results to user in natural language
```

### DAX Query Execution
```
Claude.ai User Request: "Execute this DAX query on dataset XYZ"
                          ↓
         Claude.ai processes request and extracts:
         - dataset_id
         - dax_query 
         - workspace_id (optional)
                          ↓
      Claude.ai → POST /powerbi-mcp/mcp/query
                  Body: {dataset_id, dax_query, workspace_id}
                          ↓
           API Management validates JWT + input parameters
                          ↓
         API Management → Azure Web App endpoint
                          ↓
        Azure Web App calls execute_powerbi_query()
                          ↓
       Azure Web App acquires Power BI token (client creds)
                          ↓
    Azure Web App → POST https://api.powerbi.com/v1.0/myorg/
                           datasets/{id}/executeQueries
                  Body: {queries: [{query: dax_query}]}
                          ↓
              Power BI executes DAX and returns results
                          ↓
      Azure Web App formats results with metadata:
      - query_results
      - execution_time
      - status
                          ↓
         API Management adds headers & logs execution
                          ↓
          Claude.ai receives query results
                          ↓
        Claude.ai formats and presents data to user
```

## 🛡️ Security Implementation

### Multi-Layer Security Model
```
┌─────────────────┐
│ Layer 1: HTTPS  │ ← SSL/TLS encryption for all communication
├─────────────────┤
│ Layer 2: OAuth  │ ← Microsoft Entra ID authentication
├─────────────────┤  
│ Layer 3: JWT    │ ← Token validation and claims verification
├─────────────────┤
│ Layer 4: APIM   │ ← Rate limiting, CORS, security headers
├─────────────────┤
│ Layer 5: App    │ ← Input validation, error handling
└─────────────────┘
```

### Security Policy Details

#### JWT Validation Policy
```xml
<validate-jwt header-name="Authorization" 
              failed-validation-httpcode="401">
    <openid-config url="https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration" />
    <audiences>
        <audience>{client-id}</audience>
    </audiences>
    <required-claims>
        <claim name="scp" match="any">
            <value>https://analysis.windows.net/powerbi/api/.default</value>
        </claim>
    </required-claims>
</validate-jwt>
```

#### Rate Limiting Policy
```xml
<rate-limit calls="100" renewal-period="60" />
<quota calls="10000" renewal-period="86400" />
```

#### CORS Policy
```xml
<cors allow-credentials="true">
    <allowed-origins>
        <origin>https://claude.ai</origin>
        <origin>https://api.claude.ai</origin>
    </allowed-origins>
    <allowed-methods>
        <method>GET</method>
        <method>POST</method>
        <method>OPTIONS</method>
    </allowed-methods>
</cors>
```

## 📊 Monitoring & Observability

### Request Tracking
```
Every API request generates:
┌─────────────────────────────────────────────────────────────┐
│ Correlation ID: uuid-4 format                              │
│ User Info: email, tenant, client_id                        │
│ Request Details: method, URL, headers, body size           │
│ Response Details: status_code, response_time, body_size    │
│ Security Events: JWT validation, rate limit hits           │
│ Error Details: exception type, message, stack trace        │
└─────────────────────────────────────────────────────────────┘
```

### Analytics Available
- **Request Volume:** Requests per minute/hour/day
- **Response Times:** P50, P95, P99 percentiles
- **Error Rates:** 4xx, 5xx error percentages
- **Authentication:** OAuth success/failure rates
- **Rate Limiting:** Quota usage and limit hits
- **Geographic:** Request distribution by region

## 🔄 Error Handling Strategy

### Error Flow
```
Error Occurs → Logged with Correlation ID → Structured Response → User Friendly Message
     ↓                    ↓                        ↓                     ↓
Internal     →    Azure Logs      →    API Management   →    Claude.ai
Exception         Event Hub             Error Handler         Error Display
```

### Error Response Format
```json
{
  "error": {
    "code": 500,
    "message": "Internal server error occurred",
    "correlationId": "uuid-correlation-id",
    "timestamp": "2025-07-29T12:00:00.000Z",
    "details": "Additional context for debugging"
  }
}
```

## 🚀 Performance Considerations

### Optimization Strategies
1. **Connection Pooling:** Reuse HTTP connections to Power BI
2. **Token Caching:** Cache Power BI tokens until expiration
3. **Async Processing:** Non-blocking I/O for concurrent requests
4. **Response Compression:** Gzip compression for large responses
5. **CDN Integration:** Static content delivery optimization

### Scalability Limits
- **API Management:** 1000 RPS (Developer tier), higher with Premium
- **Azure Web App:** Depends on App Service Plan
- **Power BI API:** Microsoft-enforced rate limits
- **Claude.ai:** Client-side request limitations

## 🔧 Configuration Management

### Environment-Specific Settings
```
Development:
- API Management: Developer tier
- Logging: Verbose
- Rate Limits: Relaxed
- CORS: Permissive

Production:
- API Management: Premium tier
- Logging: Error/Warning only
- Rate Limits: Strict
- CORS: Restricted domains
- Security Headers: Full suite
```

### Configuration Files
- **`mcp_api_policies.xml`:** Security policies and rules
- **`claude_enterprise_config.json`:** Claude.ai integration settings
- **Environment Variables:** Sensitive configuration (secrets, keys)
- **Named Values:** API Management configuration parameters

This architecture provides enterprise-grade security, scalability, and observability for your Power BI MCP integration with Claude.ai! 🏗️