# Power BI MCP Finance Server

An enhanced Model Context Protocol (MCP) server providing intelligent Power BI integration for financial data analysis.

## 🚀 Quick Start

### Option 1: Simplified Deployment (Recommended)
**Perfect for Azure Web App - No database dependencies**

```bash
# 1. Set critical environment variables
export POWERBI_CLIENT_ID=your-client-id
export POWERBI_CLIENT_SECRET=your-client-secret
export POWERBI_TENANT_ID=your-tenant-id
export FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# 2. Install minimal dependencies
pip install -r requirements_simple.txt

# 3. Run simplified server
python main_simple.py
```

### Option 2: Full Features
**Complete functionality with conversation tracking**

```bash
# 1. Copy environment template
cp .env.template .env

# 2. Fill in your credentials in .env file

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Run full server
python pbi_mcp_finance/main.py
```

### Option 3: Azure Web App Deployment
```bash
# Automated deployment via GitHub Actions
git push origin main

# Or manual deployment
az webapp up --name your-app-name --resource-group your-rg --runtime "PYTHON:3.11"
```

## 📚 Documentation

| File | Description |
|------|-------------|
| `AZURE_DEPLOYMENT_GUIDE.md` | Complete step-by-step deployment to Azure |
| `DEPLOYMENT_CHECKLIST.md` | Verification checklist for successful deployment |
| `ENVIRONMENT_SETUP.md` | Environment variables and configuration |

## 🏗️ Architecture

### Simplified Mode (Recommended for Azure)
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude/MCP    │───▶│   Flask + MCP    │───▶│   Power BI API  │
│   Client        │    │   (main_simple)  │    │                 │
│                 │◀───│   No Database    │◀───│ OAuth2/Token    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Full Mode (Local/Advanced)
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude/MCP    │───▶│ FastMCP + Flask  │───▶│   Power BI API  │
│   Client        │    │ + SQLite Tracking│    │                 │
│ Web Interface   │◀───│ + Monitoring     │◀───│ OAuth2/Token    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Technology Stack
- **Core**: FastMCP for Model Context Protocol
- **Web**: Flask for HTTP endpoints and optional authentication
- **Deployment**: Azure Web App (Linux, Python 3.11)
- **Database**: SQLite (full mode) or None (simplified mode)
- **Authentication**: Power BI OAuth2 + optional Azure AD web auth

## 🔧 Environment Variables

### 🚨 Critical Variables (App won't start without these)
```bash
# Power BI Authentication (choose one method)
POWERBI_CLIENT_ID=your-powerbi-app-client-id
POWERBI_CLIENT_SECRET=your-powerbi-app-client-secret  
POWERBI_TENANT_ID=your-azure-tenant-id

# OR use manual token instead
POWERBI_TOKEN=your-manual-bearer-token

# Security (required)
FLASK_SECRET_KEY=generate-32-char-random-string
```

### Optional Web Authentication
```bash
AUTH_ENABLED=true  # Enable web UI authentication
AZURE_CLIENT_ID=azure-ad-app-client-id
AZURE_CLIENT_SECRET=azure-ad-app-secret
AZURE_REDIRECT_URI=https://your-app.azurewebsites.net/auth/callback
```

### Generate Flask Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

See `.env.template` for complete configuration options.

## 🛡️ Security Features

- ✅ **OAuth2 Authorization Code Flow** with PKCE
- ✅ **CSRF Protection** with state validation
- ✅ **Secure Session Management** with configurable expiration
- ✅ **HTTPS Enforcement** with security headers
- ✅ **Token Isolation** between Power BI API and user authentication
- ✅ **Environment-based Configuration** (no hardcoded secrets)

## 🌐 Available Endpoints

### Core Endpoints (Both Modes)
| Endpoint | Description | Authentication |
|----------|-------------|----------------|
| `/` | Service status and configuration | None |
| `/health` | Health check with Power BI status | None |
| `/api/powerbi/workspaces` | List Power BI workspaces | None* |

### Web Authentication (Full Mode Only)
| Endpoint | Description | Authentication |
|----------|-------------|----------------|
| `/auth/login` | Start Microsoft OAuth login | None |
| `/auth/callback` | OAuth callback handler | None |
| `/auth/status` | Current authentication status | None |
| `/auth/logout` | Sign out and clear session | Authenticated |

### MCP Tools (Available via MCP protocol)
- Workspace discovery and management
- Dataset schema exploration  
- Financial data analysis tools
- Query optimization and recommendations

*Requires Power BI credentials to be configured

## 📁 Project Structure

```
├── main_simple.py              # 🚨 Simplified server (no database) - RECOMMENDED
├── requirements_simple.txt     # 🚨 Minimal dependencies for Azure
├── pbi_mcp_finance/            # Full server with all features
│   ├── main.py                 # Full MCP server with database
│   ├── auth/                   # Authentication modules
│   ├── mcp/tools/              # MCP tool implementations
│   └── database/               # SQLite database modules
├── requirements.txt            # Full dependencies (includes database)
├── .env.template              # Environment variables template
├── startup.sh                 # Azure startup script (auto-detects mode)
├── web.config                 # Azure Web App configuration
└── .github/workflows/         # GitHub Actions for deployment
```

## 🚀 Deployment Modes

### Mode 1: Simplified (Recommended for Azure)
✅ **No database dependencies**  
✅ **Faster startup and deployment**  
✅ **Perfect for cloud environments**  
❌ No conversation tracking  
❌ No performance metrics  

### Mode 2: Full Featured (Local/Advanced)
✅ **Complete MCP functionality**  
✅ **SQLite conversation tracking**  
✅ **Performance monitoring**  
❌ Requires SQLite database setup  
❌ More complex deployment  

### Local Development
```bash
# Option 1: Test simplified version
python main_simple.py

# Option 2: Test full version
cp .env.template .env
# Fill in credentials
python pbi_mcp_finance/main.py
```

## 🧪 Testing

### Test Environment Configuration
```bash
# Test your environment setup
python test_env_simple.py

# Expected output: Shows which variables are set/missing
```

### Test Endpoints
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test Power BI status (requires credentials)
curl http://localhost:8000/api/powerbi/workspaces
```

## 🔧 Troubleshooting

### Deployment Issues

**GitHub Actions Artifact Storage Quota**
- ✅ **Fixed**: Updated workflow deploys directly without artifacts

**Azure Web App Won't Start**
- Check Application Logs in Azure Portal
- Verify environment variables are set correctly
- Ensure startup command is `/home/site/wwwroot/startup.sh`

**Database Errors**
- ✅ **Fixed**: Use simplified mode (`main_simple.py`) - no database required

### Authentication Issues

**Power BI Authentication Failed**
- Verify `POWERBI_CLIENT_ID`, `POWERBI_CLIENT_SECRET`, `POWERBI_TENANT_ID`
- Check Azure AD app registration permissions
- Try manual token: Set `POWERBI_TOKEN` instead

**Flask Secret Key Missing**
- Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Add to Azure App Settings or .env file

## 🎯 Next Steps

1. **Quick Test**: Run `python main_simple.py` locally
2. **Configure**: Set the 4 critical environment variables 🚨
3. **Deploy**: Push to main branch or use Azure CLI
4. **Verify**: Check `/health` endpoint after deployment
5. **Use**: Connect Claude with MCP to your deployed server

## 📚 Additional Documentation

- [Environment Setup Guide](ENVIRONMENT_SETUP.md) - Detailed variable configuration
- [Azure Deployment Guide](AZURE_DEPLOYMENT_GUIDE.md) - Step-by-step deployment
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md) - Pre-deployment verification

---

**🚀 Ready to deploy your Power BI MCP server to Azure!**