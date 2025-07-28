# 🔐 MCP Server Authentication Options for Claude.ai

## Current Challenge

You have a multi-tenant Power BI environment where:
- Multiple clients with separate workspaces
- Each client should only access their own Power BI data
- Claude.ai needs to connect to your MCP server with proper user authentication
- Microsoft authentication is required for security compliance

## Authentication Options for MCP Servers

### Option 1: OAuth 2.0 Flow (Recommended for Multi-Tenant)

**How it Works:**
- Claude.ai acts as OAuth client
- Users authenticate with Microsoft directly
- MCP server receives user-specific access tokens
- Each user only sees their own Power BI workspaces

**Implementation:**
```
User → Claude.ai → Microsoft OAuth → MCP Server
                     ↓
               User's PBI Token → Power BI API
```

**Pros:**
- ✅ True multi-tenant security
- ✅ Users authenticate with their own Microsoft accounts
- ✅ Delegated permissions (user's actual PBI access)
- ✅ Audit trail under user identity
- ✅ No shared credentials

**Cons:**
- ❌ Complex implementation
- ❌ Requires OAuth flow in Claude.ai
- ❌ Token management complexity

**Claude.ai Setup:**
```
Server Name: Power BI Finance Server
Remote URL: https://pbimcp.azurewebsites.net
OAuth Client ID: your-azure-app-id
OAuth Client Secret: your-azure-app-secret
```

### Option 2: Service Principal with Workspace Mapping

**How it Works:**
- Single service principal for MCP server
- User identity passed via custom headers
- MCP server maps users to their workspaces
- Service principal has read access to all workspaces

**Implementation:**
```
User → Claude.ai → MCP Server (+ User Header)
                      ↓
               Service Principal → Power BI API
                      ↓
               Filter by User's Workspaces
```

**Pros:**
- ✅ Simpler than OAuth
- ✅ Centralized service account
- ✅ User-specific data filtering
- ✅ Works with current Claude.ai

**Cons:**
- ❌ Service account needs broad permissions
- ❌ Custom user mapping required
- ❌ Less secure than delegated access

**Claude.ai Setup:**
```
Server Name: Power BI Finance Server
Remote URL: https://pbimcp.azurewebsites.net
Custom Headers: X-User-Email: {user.email}
API Key: your-service-principal-key
```

### Option 3: Pre-Authenticated Token Approach

**How it Works:**
- Users get their own MCP server instances
- Each instance pre-configured with user's token
- Separate MCP endpoints per user/client
- Static authentication per instance

**Implementation:**
```
Client A → https://pbimcp.azurewebsites.net/client-a
Client B → https://pbimcp.azurewebsites.net/client-b
                         ↓
               Pre-configured User Tokens → Power BI API
```

**Pros:**
- ✅ Complete data isolation
- ✅ Simple Claude.ai setup
- ✅ No runtime authentication
- ✅ Highest security

**Cons:**
- ❌ Requires separate configurations per client
- ❌ Token refresh complexity
- ❌ Multiple deployments

### Option 4: Microsoft Entra ID App Proxy

**How it Works:**
- Azure AD Application Proxy in front of MCP server
- Users authenticate via Microsoft before reaching MCP
- MCP server receives authenticated user context
- Single sign-on experience

**Implementation:**
```
User → Claude.ai → Azure AD Proxy → MCP Server
                      ↓
               User Context → Power BI API
```

**Pros:**
- ✅ Enterprise-grade security
- ✅ Single sign-on
- ✅ User context automatically passed
- ✅ Centralized access control

**Cons:**
- ❌ Requires Azure AD Premium
- ❌ Complex Azure setup
- ❌ May not work with Claude.ai's HTTP calls

## Recommended Solution: OAuth 2.0 with Fallbacks

### Phase 1: OAuth Implementation (Ideal)

1. **Azure App Registration:**
   - Delegated permissions for Power BI
   - Multi-tenant if needed
   - Proper redirect URLs

2. **MCP Server Updates:**
   - OAuth endpoint handlers
   - Token validation
   - User-specific Power BI calls

3. **Claude.ai Configuration:**
   - OAuth client credentials
   - Automatic token refresh

### Phase 2: Service Principal Fallback (If OAuth Fails)

1. **Service Principal Setup:**
   - Power BI service admin permissions
   - Read access to all client workspaces

2. **User Mapping Database:**
   - User email → Workspace IDs mapping
   - Role-based access control

3. **MCP Server Enhancement:**
   - User identity extraction
   - Workspace filtering logic

### Phase 3: Per-Client Instances (Maximum Security)

1. **Deployment Templates:**
   - Parameterized ARM templates
   - Client-specific configurations

2. **Token Management:**
   - Automated token refresh
   - Secure storage

## Implementation Priority

### Immediate (Week 1-2):
- **Service Principal + User Mapping** (Option 2)
- Test with 2-3 clients
- Validate workspace isolation

### Short-term (Week 3-4):
- **OAuth 2.0 Implementation** (Option 1)
- Pilot with select users
- Refine authentication flow

### Long-term (Month 2+):
- **Per-Client Instances** (Option 3)
- Enterprise deployment
- Full security compliance

## Technical Requirements

### For OAuth (Option 1):
```bash
# Azure App Registration
- Delegated Permissions: Dataset.Read.All, Report.Read.All, Workspace.Read.All
- Redirect URI: https://pbimcp.azurewebsites.net/auth/callback
- Multi-tenant: Yes (if cross-tenant clients)

# Environment Variables
AZURE_CLIENT_ID=your-app-id
AZURE_CLIENT_SECRET=your-app-secret  
AZURE_TENANT_ID=your-tenant-id
```

### For Service Principal (Option 2):
```bash
# Service Principal Setup
- Power BI Admin Portal: Enable service principal access
- Workspace permissions: Member/Admin on all client workspaces
- API access: PowerBI-API permissions

# Environment Variables  
POWERBI_CLIENT_ID=service-principal-id
POWERBI_CLIENT_SECRET=service-principal-secret
POWERBI_TENANT_ID=your-tenant-id
USER_WORKSPACE_MAPPING=database-connection-string
```

## Security Considerations

### Data Isolation:
- ✅ Row-level security in Power BI
- ✅ Workspace-level permissions
- ✅ API-level filtering
- ✅ Audit logging

### Token Security:
- ✅ Short-lived access tokens
- ✅ Secure token storage
- ✅ Automatic token refresh
- ✅ Token revocation capability

### Compliance:
- ✅ Microsoft security standards
- ✅ Enterprise identity integration
- ✅ Activity logging
- ✅ Access reviews

## Next Steps

1. **Choose Primary Option**: OAuth 2.0 (recommended)
2. **Create Azure App Registration**: For delegated permissions
3. **Update MCP Server**: Add OAuth endpoints
4. **Test with Pilot Users**: Validate authentication flow
5. **Deploy to Production**: Roll out to all clients

Would you like me to implement any of these options?