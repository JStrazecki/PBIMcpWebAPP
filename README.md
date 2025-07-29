# 🚀 Power BI MCP Enterprise Integration

Enterprise-grade Power BI Model Context Protocol (MCP) server for Claude.ai integration with Azure API Management security.

## 🎯 Quick Start

### ⚡ **Fully Automated Deployment (Recommended)**
```bash
cd api-management
./deploy_complete_automation.sh
```
**Zero manual configuration** - pulls everything from your Azure Web App environment variables!

### 📚 **Need Help?**
See: [`documentation/COMPLETE_SETUP_GUIDE.md`](documentation/COMPLETE_SETUP_GUIDE.md)

## 📁 Project Structure

```
├── 🏗️ api-management/           # API Management deployment scripts
│   ├── deploy_complete_automation.sh    # ⚡ Main automation (recommended)
│   ├── deploy_apim0.sh                  # Manual API Management setup
│   ├── configure_oauth0.sh              # Manual OAuth configuration
│   └── README.md                        # Complete usage guide
│
├── 💻 local-development/        # Local development & testing
│   ├── setup_local_mcp.bat             # Local MCP server setup
│   ├── claude_desktop_config.json      # Claude Desktop config
│   └── README.md
│
├── ☁️ azure-deployment/         # Azure Web App deployment
│   ├── startup.sh                      # Comprehensive startup script
│   ├── gunicorn.conf.py                # Production WSGI config
│   └── README.md
│
├── 📚 documentation/            # All documentation
│   ├── COMPLETE_SETUP_GUIDE.md         # 📖 Main setup guide
│   ├── AUTOMATED_DEPLOYMENT_GUIDE.md   # ⚡ Automation guide
│   ├── CLAUDE_ENTERPRISE_SETUP_FAQ.md  # 🏢 Enterprise FAQ
│   └── README.md
│
├── 🐍 Application Files
│   ├── mcp_bridge.py                   # Main HTTP-to-MCP bridge
│   ├── mcp_server.py                   # Pure MCP server (local dev)
│   ├── requirements.txt                # Python dependencies
│   └── pbi_mcp_finance/               # Core application modules
│
└── ⚙️ Configuration
    ├── startup.txt                     # Azure startup command
    ├── claude_enterprise_config.json   # Claude.ai Enterprise config
    └── CLEANUP_PLAN.md                # Repository cleanup documentation
```

## 🎯 Choose Your Path

### 🏢 **Enterprise Production Deployment**
```bash
cd api-management
./deploy_complete_automation.sh
```
**Result**: Enterprise-grade API Management with OAuth 2.0, rate limiting, and security policies.

### 💻 **Local Development**
```bash
cd local-development
setup_local_mcp.bat  # Windows
```
**Result**: Local MCP server for Claude Desktop development.

### 📚 **Need Documentation?**
```bash
cd documentation
# See COMPLETE_SETUP_GUIDE.md for comprehensive instructions
```

## 🏗️ Architecture

```
Claude.ai Enterprise
    ↓ OAuth 2.0 Authentication
Azure API Management (Security Gateway)
    ↓ JWT Validation + Rate Limiting + CORS
Azure Web App (MCP Bridge Server)
    ↓ Client Credentials OAuth
Power BI REST API
    ↓ Direct Access
Your Power BI Workspaces & Datasets
```

## ✨ Key Features

- **🔒 Enterprise Security**: OAuth 2.0, JWT validation, rate limiting
- **⚡ Zero Configuration**: Auto-detects settings from Azure Web App
- **🌐 Claude.ai Integration**: Native MCP protocol support
- **📊 Power BI Access**: Full workspace and dataset access
- **🛡️ CORS Protection**: Secure cross-origin requests
- **📈 Monitoring**: Request logging and analytics
- **🔄 Auto-Deploy**: GitHub integration with Azure Web Apps

## 🚀 Quick Commands

| Task | Command | Directory |
|------|---------|-----------|
| **Deploy Everything** | `./deploy_complete_automation.sh` | `api-management/` |
| **Local Development** | `setup_local_mcp.bat` | `local-development/` |
| **Read Main Guide** | Open `COMPLETE_SETUP_GUIDE.md` | `documentation/` |
| **Test Integration** | `./test_integration.sh` | `api-management/` |

## 🔧 Environment Variables Required

Your Azure Web App must have these environment variables set:

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `AZURE_TENANT_ID` | Azure tenant ID | Azure Portal → App Registrations → Overview |
| `AZURE_CLIENT_ID` | App registration client ID | Azure Portal → App Registrations → Overview |
| `AZURE_CLIENT_SECRET` | App registration secret | Azure Portal → App Registrations → Certificates & secrets |

## 🛠️ Available MCP Tools

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `get_powerbi_status` | Server health and auth status | "Check Power BI connection status" |
| `list_powerbi_workspaces` | List accessible workspaces | "Show me all Power BI workspaces" |
| `get_powerbi_datasets` | List datasets in workspaces | "What datasets are in my workspace?" |
| `execute_powerbi_query` | Run DAX queries | "Execute this DAX query: EVALUATE..." |
| `health_check` | System health monitoring | Automatic health monitoring |

## 📞 Support & Documentation

- 📖 **Complete Setup**: [`documentation/COMPLETE_SETUP_GUIDE.md`](documentation/COMPLETE_SETUP_GUIDE.md)
- ⚡ **Automation Guide**: [`documentation/AUTOMATED_DEPLOYMENT_GUIDE.md`](documentation/AUTOMATED_DEPLOYMENT_GUIDE.md)
- 🏢 **Enterprise FAQ**: [`documentation/CLAUDE_ENTERPRISE_SETUP_FAQ.md`](documentation/CLAUDE_ENTERPRISE_SETUP_FAQ.md)
- 🔧 **Troubleshooting**: [`documentation/STARTUP_ISSUES_ANALYSIS.md`](documentation/STARTUP_ISSUES_ANALYSIS.md)

## 🎉 Success Criteria

Your setup is complete when:
- ✅ Azure Web App is deployed and running
- ✅ API Management is configured with OAuth 2.0
- ✅ Claude.ai Enterprise can authenticate and access Power BI
- ✅ All security policies are active (rate limiting, CORS, JWT validation)

---

**🚀 Ready to deploy?** Start with [`api-management/deploy_complete_automation.sh`](api-management/) for zero-configuration setup!