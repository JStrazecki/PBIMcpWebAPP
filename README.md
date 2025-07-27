# Power BI MCP Finance Web App

Microsoft Azure AD authenticated web application for Power BI Model Context Protocol (MCP) server.

## 🚀 Features

- 🔐 **Microsoft Azure AD OAuth2** - Enterprise authentication
- 📊 **Power BI API Integration** - Direct workspace and dataset access
- 🌐 **Web-based MCP Tools** - Browser access to all MCP functionality
- ☁️ **Azure Web App Ready** - One-click deployment to Azure
- 🛡️ **Enterprise Security** - Session management and secure tokens
- 📈 **Real-time Monitoring** - Application health and performance tracking

## 📋 Quick Deployment

### 1. Deploy to Azure Web App
```bash
# Follow the comprehensive guide
AZURE_DEPLOYMENT_GUIDE.md
```

### 2. Configure Authentication
```bash
# Create Azure AD app registration
# Add environment variables to Azure Web App
# See: ENVIRONMENT_SETUP.md
```

### 3. Access Your Application
```
https://your-webapp.azurewebsites.net/auth/login
```

## 📚 Documentation

| File | Description |
|------|-------------|
| `AZURE_DEPLOYMENT_GUIDE.md` | Complete step-by-step deployment to Azure |
| `DEPLOYMENT_CHECKLIST.md` | Verification checklist for successful deployment |
| `ENVIRONMENT_SETUP.md` | Environment variables and configuration |

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │───▶│   Azure Web App  │───▶│   Power BI API  │
│                 │    │                  │    │                 │
│ Microsoft Login │◀───│ OAuth2 + Flask   │◀───│ Service Principal│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Technology Stack
- **Frontend**: Flask with Microsoft OAuth2 integration
- **Backend**: Power BI MCP server with enhanced authentication  
- **Deployment**: Azure Web App (Linux, Python 3.11)
- **Authentication**: Azure Active Directory with secure sessions
- **API**: Power BI REST API with automatic token management

## 🔧 Environment Variables

### Required for Authentication
```bash
AUTH_ENABLED=true
AZURE_CLIENT_ID=<azure-ad-app-client-id>
AZURE_CLIENT_SECRET=<azure-ad-app-secret>
AZURE_TENANT_ID=<your-tenant-id>
FLASK_SECRET_KEY=<random-32-chars>
```

### Required for Power BI
```bash
POWERBI_CLIENT_ID=<power-bi-service-principal-id>
POWERBI_CLIENT_SECRET=<power-bi-service-principal-secret>
POWERBI_TENANT_ID=<your-tenant-id>
```

See `.env.template` for complete configuration.

## 🛡️ Security Features

- ✅ **OAuth2 Authorization Code Flow** with PKCE
- ✅ **CSRF Protection** with state validation
- ✅ **Secure Session Management** with configurable expiration
- ✅ **HTTPS Enforcement** with security headers
- ✅ **Token Isolation** between Power BI API and user authentication
- ✅ **Environment-based Configuration** (no hardcoded secrets)

## 🌐 Available Endpoints

| Endpoint | Description | Authentication |
|----------|-------------|----------------|
| `/` | Health check and application status | None |
| `/health` | Detailed health information | None |
| `/auth/login` | Start Microsoft OAuth login | None |
| `/auth/callback` | OAuth callback handler | None |
| `/auth/status` | Current authentication status | None |
| `/auth/logout` | Sign out and clear session | Authenticated |
| MCP Tools | All Power BI MCP functionality | Authenticated |

## 🚀 Deployment Options

### Azure Web App (Recommended)
- Built-in HTTPS and custom domains
- Automatic scaling and load balancing
- Integrated with Azure Active Directory
- Application Insights monitoring

### Local Development
```bash
# Copy environment template
cp .env.template .env

# Fill in your credentials
# Set AUTH_ENABLED=false for local testing

# Run the application
python -m pbi_mcp_finance.main
```

## 📊 Monitoring

The application includes:
- **Health check endpoints** for Azure monitoring
- **Structured logging** with configurable levels
- **Application metrics** and performance tracking
- **Authentication audit trail**
- **Power BI API call monitoring**

## 🔄 Development Workflow

1. **Local Development**: `AUTH_ENABLED=false` for testing without OAuth
2. **Staging**: Deploy with authentication to test OAuth flow
3. **Production**: Full deployment with monitoring and scaling

## 📞 Support

### Troubleshooting
- Check Azure Web App logs for deployment issues
- Verify environment variables are set correctly
- Ensure Azure AD app permissions are granted
- Validate Power BI service principal access

### Common Issues
- **OAuth redirect mismatch**: Check redirect URI matches exactly
- **Power BI access denied**: Verify service principal permissions
- **Session expired**: Check `FLASK_SECRET_KEY` consistency
- **Build failures**: Review `requirements.txt` dependencies

---

## 🎯 Getting Started

1. **Deploy**: Follow `AZURE_DEPLOYMENT_GUIDE.md`
2. **Configure**: Set environment variables per `ENVIRONMENT_SETUP.md`
3. **Test**: Visit `/auth/login` to verify authentication
4. **Use**: Access authenticated MCP tools via web interface

**Enterprise-ready Power BI web access with Microsoft authentication!** 🎉