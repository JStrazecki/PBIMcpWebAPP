# 🔐 OAuth 2.0 Implementation Guide - Power BI MCP Server

## 🎯 Overview

Your MCP server implements **OAuth 2.0 with Microsoft authentication** for secure, user-specific Power BI access. Each user authenticates with their Microsoft account and gets access to **only their authorized Power BI resources**.

## 🔑 Key Security Principle

**Users see only their own workspaces - App Registration defines capabilities, User permissions determine access!**

```
App Registration: Grants permission TYPES ("can read workspaces")
User Permissions: Determines WHICH workspaces user can access
Final Result: Intersection of both = User's actual accessible data
```

## 🏗️ Architecture

```
User → Claude.ai → Microsoft OAuth → MCP Server → Power BI API
   ↓           ↓           ↓            ↓           ↓
Browser   HTTP Req   Access Token   On-Behalf-Of   User Data
                                                       ↓
                                            Only user's workspaces
```

## ⚙️ Step 1: Azure App Registration Setup

### 1.1 Create App Registration

1. Go to **Azure Portal** → **App registrations** → **New registration**
2. Fill in:
   - **Name**: `Power BI MCP Server OAuth`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: 
     - Type: `Web`
     - URL: `https://pbimcp.azurewebsites.net/auth/callback`
3. Click **Register**

### 1.2 Configure API Permissions

1. Go to **API permissions** → **Add a permission**
2. Select **Power BI Service** → **Delegated permissions**
3. Add these permissions:
   - ✅ `Dataset.Read.All`
   - ✅ `Report.Read.All`
   - ✅ `Workspace.Read.All`
   - ✅ `Content.Create` (optional, for advanced features)

4. Click **Grant admin consent** (requires tenant admin)
5. Verify status shows \"Granted\" with green checkmarks

### 1.3 Get Credentials

1. **Overview tab** → Copy these values:\n   - 📋 **Application (client) ID**\n   - 📋 **Directory (tenant) ID**\n\n2. **Certificates & secrets** → **New client secret**:\n   - **Description**: `MCP Server OAuth Secret`\n   - **Expires**: `24 months`\n   - 📋 Copy the **Value** (not the Secret ID)\n\n⚠️ **Important**: Save the client secret value immediately - it won't be shown again!\n\n## ⚙️ Step 2: Azure Web App Configuration\n\nAdd these environment variables in **Azure Portal** → **pbimcp** → **Configuration** → **Application Settings**:\n\n```bash\nAZURE_CLIENT_ID=your-application-client-id\nAZURE_CLIENT_SECRET=your-client-secret-value\nAZURE_TENANT_ID=your-directory-tenant-id\nREDIRECT_URI=https://pbimcp.azurewebsites.net/auth/callback\n```\n\n**Click Save** and **Restart** the Web App.\n\n## ⚙️ Step 3: Deploy Updated Code\n\nCommit and push the OAuth-enabled code:\n\n```bash\ngit add .\ngit commit -m \"Implement OAuth 2.0 authentication for multi-tenant Power BI access\"\ngit push\n```\n\nWait for GitHub Actions deployment to complete (~3-5 minutes).\n\n## 🧪 Step 4: Test OAuth Flow\n\n### 4.1 Test Authentication URL\n\n```bash\ncurl https://pbimcp.azurewebsites.net/auth/url\n```\n\n**Expected Response:**\n```json\n{\n  \"auth_url\": \"https://login.microsoftonline.com/your-tenant/oauth2/v2.0/authorize?client_id=...\",\n  \"message\": \"Visit the auth_url to authenticate with Microsoft\"\n}\n```\n\n### 4.2 Test User Authentication Flow\n\n1. **Get Auth URL**: `GET https://pbimcp.azurewebsites.net/auth/url`\n2. **User Login**: Visit the returned `auth_url` in browser\n3. **Microsoft Login**: User signs in with their Microsoft account\n4. **Grant Permissions**: User authorizes Power BI access\n5. **Get Token**: User gets redirected to callback with access token\n\n### 4.3 Test MCP Tools with Token\n\n```bash\n# Use the access_token from step 4.2\ncurl -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\" \\\n     https://pbimcp.azurewebsites.net/mcp/get_powerbi_status\n```\n\n**Expected Response:**\n```json\n{\n  \"user\": {\n    \"email\": \"user@company.com\",\n    \"name\": \"John Doe\",\n    \"user_id\": \"12345678-1234-1234-1234-123456789012\"\n  },\n  \"powerbi_access\": \"granted\",\n  \"server_status\": \"running\",\n  \"authentication\": \"oauth2_microsoft\"\n}\n```\n\n## 🔗 Step 5: Claude.ai MCP Configuration\n\n### 5.1 Add MCP Server in Claude.ai\n\n1. Go to **Claude.ai** → **Settings** → **MCP Servers**\n2. Click **Add Custom Connector**\n3. Fill in:\n\n```\nServer Name: Power BI Finance Server (OAuth)\nRemote MCP Server URL: https://pbimcp.azurewebsites.net\nOAuth Client ID: your-azure-app-client-id\nOAuth Client Secret: your-azure-app-client-secret\nDescription: Multi-tenant Power BI server with user-specific access\n```\n\n### 5.2 Authentication Flow in Claude.ai\n\n1. **User connects**: Claude.ai detects OAuth configuration\n2. **Redirect to Microsoft**: User gets redirected to Microsoft login\n3. **User authenticates**: Signs in with their Microsoft account\n4. **Permission grant**: User authorizes Claude.ai to access Power BI\n5. **Token exchange**: Claude.ai receives user's access token\n6. **MCP access**: User can now use Power BI tools through Claude\n\n## 🛠️ Available MCP Tools (OAuth-Protected)\n\nAll tools now require valid Microsoft authentication:\n\n| Tool | Description | User-Specific |\n|------|-------------|---------------|\n| `get_powerbi_status` | Check user's Power BI access | ✅ |\n| `health_check` | Server health with user info | ✅ |\n| `list_powerbi_workspaces` | List user's accessible workspaces | ✅ |\n| `get_powerbi_datasets` | Get datasets from user's workspaces | ✅ |\n| `execute_powerbi_query` | Run DAX queries with user permissions | ✅ |\n\n## 🔒 Security Features\n\n### Multi-Tenant Security:\n- ✅ **User isolation**: Each user sees only their own data\n- ✅ **Delegated permissions**: Uses user's actual Power BI access\n- ✅ **Token-based auth**: Secure OAuth 2.0 flow\n- ✅ **No shared credentials**: No service account needed\n- ✅ **Audit trail**: All actions logged under user identity\n\n### Token Security:\n- ✅ **Short-lived tokens**: 1-hour expiration\n- ✅ **Scope-limited**: Only requested Power BI permissions\n- ✅ **On-behalf-of flow**: Server acts on user's behalf\n- ✅ **Secure transmission**: HTTPS only\n\n## 🧪 Testing Multi-Tenant Access\n\n### Test with Different Users:\n\n```bash\n# User A authenticates and gets their token\nUSER_A_TOKEN=\"eyJ0eXAiOiJKV1QiLCJhbGc...\"\n\n# User B authenticates and gets their token  \nUSER_B_TOKEN=\"eyJ0eXAiOiJKV1QiLCJub3Q...\"\n\n# Test User A's workspaces\ncurl -H \"Authorization: Bearer $USER_A_TOKEN\" \\\n     https://pbimcp.azurewebsites.net/mcp/list_powerbi_workspaces\n\n# Test User B's workspaces\ncurl -H \"Authorization: Bearer $USER_B_TOKEN\" \\\n     https://pbimcp.azurewebsites.net/mcp/list_powerbi_workspaces\n```\n\n**Result**: Each user will see only their own workspaces! 🎉\n\n## 🚨 Troubleshooting\n\n### Common Issues:\n\n**\"OAuth not configured\" Error:**\n- ✅ Check Azure Web App environment variables\n- ✅ Verify all 4 OAuth variables are set\n- ✅ Restart Web App after adding variables\n\n**\"Authentication required\" Error:**\n- ✅ Include `Authorization: Bearer <token>` header\n- ✅ Verify token hasn't expired (1 hour limit)\n- ✅ Re-authenticate if token is expired\n\n**\"Power BI API error\":**\n- ✅ Verify user has Power BI Pro/Premium license\n- ✅ Check user has access to requested workspaces\n- ✅ Confirm admin consent was granted for API permissions\n\n**\"Unable to access Power BI on behalf of user\":**\n- ✅ Verify on-behalf-of flow is working\n- ✅ Check Power BI service permissions\n- ✅ Ensure user token includes required scopes\n\n### Debug Endpoints:\n\n```bash\n# Check server configuration\ncurl https://pbimcp.azurewebsites.net/\n\n# Check health status\ncurl https://pbimcp.azurewebsites.net/health\n\n# Get authentication URL\ncurl https://pbimcp.azurewebsites.net/auth/url\n```\n\n## 🎉 Success Indicators\n\n✅ **Server responds with OAuth configuration**  \n✅ **Users can get authentication URLs**  \n✅ **Microsoft login redirects work**  \n✅ **Access tokens are issued**  \n✅ **MCP tools return user-specific data**  \n✅ **Different users see different workspaces**  \n✅ **Claude.ai can connect and authenticate users**  \n\n## 🚀 Next Steps\n\n1. **Test with pilot users** from different departments\n2. **Verify workspace isolation** between clients\n3. **Monitor authentication flow** in production\n4. **Scale to all users** once validated\n5. **Add refresh token flow** for better UX (optional)\n\n## 📚 Key Permission Concepts

### 🔑 Delegated Permissions Explained

**App Registration Permissions**: Define what TYPES of actions are allowed
- `Dataset.Read.All` = "App can read datasets on behalf of user"
- `Workspace.Read.All` = "App can read workspaces on behalf of user"

**User Permissions**: Determine WHICH specific resources user can access
- User A has access to "Sales Dashboard" workspace
- User B has access to "Marketing Reports" workspace

**Final Result**: Intersection of both = User's actual accessible data
- User A will only see "Sales Dashboard" (even if app has broader permissions)
- User B will only see "Marketing Reports" (even if app has broader permissions)

### 🎯 Permission Scenarios

| App Registration | User Permission | Final Access | Why? |
|------------------|-----------------|--------------|------|
| Workspaces A, B, C | Workspace A | **Workspace A** | User limited by their access |
| Workspace A | Workspaces A, B | **Workspace A** | User limited by app scope |
| Workspaces A, B | Workspaces B, C | **Workspace B** | Intersection of permissions |

📖 **For detailed scenarios**: See `OAUTH_ACCESS_SCENARIOS.md`

## 📚 Additional Resources

- 📖 **`OAUTH_ACCESS_SCENARIOS.md`** - Detailed permission scenarios and troubleshooting
- 🔧 **`MCP_AUTHENTICATION_OPTIONS.md`** - Alternative authentication approaches  
- 🚀 **`CLAUDE_MCP_SETUP_GUIDE.md`** - Claude.ai integration guide

## 🎯 Multi-Tenant Validation Checklist

✅ **User A** can only see their authorized workspaces  
✅ **User B** sees different workspaces than User A  
✅ **Admin users** see appropriate workspaces (not necessarily all)  
✅ **No user** can access workspaces they don't have Power BI permissions for  
✅ **Permission changes** in Power BI immediately affect MCP access  
✅ **App registration** limits maximum possible permissions  
✅ **User permissions** determine actual accessible resources  

Your Power BI MCP server now provides enterprise-grade, multi-tenant authentication with perfect user isolation! 🔐✨