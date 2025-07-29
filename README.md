# Power BI MCP Server for Claude.ai Enterprise

Enterprise-grade Model Context Protocol (MCP) server that provides secure access to Power BI workspaces and datasets through Claude.ai Enterprise, powered by Azure API Management.

## 🎯 What This Does

Enables Claude.ai Enterprise users to:
- 📊 **Query Power BI workspaces and datasets** using natural language
- 🔍 **Execute DAX queries** directly from Claude.ai conversations  
- 📈 **Analyze Power BI data** with AI-powered insights
- 🔐 **Secure enterprise access** through OAuth 2.0 and Azure API Management

## 🏗️ Architecture

```
Claude.ai Enterprise → Azure API Management → Azure Web App → Power BI REST API
                      (OAuth + Security)    (MCP Bridge)    (Your Data)
```

## 🚀 Quick Start

### Prerequisites
- Azure subscription
- Claude.ai Enterprise account
- Power BI workspaces with data
- Azure App Registration (OAuth configured)

### 5-Minute Setup
```bash
# 1. Deploy API Management (15-30 minutes)
.\deploy_apim.bat

# 2. Configure OAuth
./configure_oauth_apim.sh

# 3. Create MCP API
./create_mcp_api.sh

# 4. Apply security policies
./apply_policies.sh

# 5. Test integration
./test_apim_integration.sh
```

**📚 [Complete Setup Guide](COMPLETE_SETUP_GUIDE.md)** - Detailed step-by-step instructions

## 📁 Repository Structure

### 🎯 Core Application
```
mcp_bridge.py           # Main HTTP-to-MCP bridge server (production)
mcp_server.py          # Pure MCP server (local development)
requirements.txt       # Python dependencies
startup.sh            # Azure Web App startup script
```

### 🏗️ Azure API Management (Enterprise Solution)
```
deploy_apim.bat/.sh           # Deploy API Management instance
configure_oauth_apim.sh       # Configure OAuth 2.0 with Entra ID
create_mcp_api.sh            # Create MCP API and endpoints
apply_policies.sh            # Apply security policies
mcp_api_policies.xml         # Security policy definitions
test_apim_integration.sh     # Integration testing
```

### ⚙️ Configuration
```
claude_enterprise_config.json    # Claude.ai Enterprise integration config
claude_desktop_config.json      # Claude Desktop local config  
setup_local_mcp.bat             # Local development setup
gunicorn.conf.py                # Web server configuration
```

### 📚 Documentation
```
COMPLETE_SETUP_GUIDE.md         # Step-by-step setup instructions
ARCHITECTURE_AND_WORKFLOW.md    # Technical architecture details
APIM_DEPLOYMENT_COMPLETE.md     # Enterprise deployment guide
```

### 🧩 Power BI Integration
```
pbi_mcp_finance/               # Core business logic package
├── auth/                      # OAuth and authentication
├── config/                    # Configuration management  
├── mcp/tools/                # MCP tool implementations
├── powerbi/                  # Power BI API client
└── utils/                    # Utilities and helpers
```

## 🔐 Security Features

- ✅ **OAuth 2.0 Authentication** with Microsoft Entra ID
- ✅ **JWT Token Validation** for all API calls
- ✅ **Rate Limiting** (100 req/min, 10K req/day)
- ✅ **CORS Configuration** for Claude.ai domains
- ✅ **Security Headers** (XSS, CSRF protection)
- ✅ **Audit Logging** for all requests and responses
- ✅ **HTTPS Only** communication

## 🛠️ Available MCP Tools

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `get_powerbi_status` | Server health and auth status | "Check Power BI connection status" |
| `list_powerbi_workspaces` | List accessible workspaces | "Show me all Power BI workspaces" |
| `get_powerbi_datasets` | List datasets in workspaces | "What datasets are in my workspace?" |
| `execute_powerbi_query` | Run DAX queries | "Execute this DAX query: EVALUATE..." |
| `health_check` | System health monitoring | Automatic health monitoring |

## 🧪 Testing

### Local Testing
```bash
# Test MCP bridge locally
python -c "from mcp_bridge import app; print('MCP bridge working!')"

# Test pure MCP server
python mcp_server.py
```

### Production Testing
```bash
# Test API Management endpoints
curl https://your-gateway-url/powerbi-mcp/health

# Run full integration test
./test_apim_integration.sh
```

## 📊 Monitoring

Access via Azure Portal:
- **API Analytics:** Request volume, response times, error rates
- **Security Events:** OAuth flows, JWT validation, rate limiting
- **Audit Logs:** Complete request/response tracking
- **Performance Metrics:** P50/P95/P99 response times

## 🔧 Configuration

### Environment Variables (Azure App Service)
```
AZURE_CLIENT_ID=your-app-registration-client-id
AZURE_CLIENT_SECRET=your-app-registration-client-secret  
AZURE_TENANT_ID=your-azure-tenant-id
FLASK_SECRET_KEY=your-flask-secret-key
```

### Claude.ai Enterprise Setup
1. Navigate to Claude.ai Enterprise → Integrations
2. Add MCP Server integration
3. Use OAuth configuration from `claude_enterprise_config.json`
4. Test connection with "Show me Power BI workspaces"

## 🆘 Troubleshooting

### Common Issues

**"Error connecting to PowerBIMCP"**
- Check OAuth redirect URIs in app registration
- Verify API Management security policies applied
- Test backend server health: `/health` endpoint

**"Authentication failed"**  
- Verify app registration permissions
- Check JWT token validation in API Management
- Confirm OAuth 2.0 server configuration

**"Rate limit exceeded"**
- Monitor API Management analytics
- Adjust rate limits in `mcp_api_policies.xml`
- Consider upgrading API Management tier

### Debug Commands
```bash
# Check backend server
curl https://pbimcp.azurewebsites.net/health

# Test OAuth flow manually  
curl "https://your-gateway/powerbi-mcp/authorize?response_type=code&client_id=YOUR-ID"

# View API Management logs
az apim logger show --resource-group rg-pbi-mcp-enterprise --service-name YOUR-APIM-NAME
```

## 🚀 Production Deployment Checklist

- ✅ Azure API Management deployed with security policies
- ✅ App registration redirect URIs updated
- ✅ Environment variables configured in Azure App Service
- ✅ Claude.ai Enterprise integration configured
- ✅ End-to-end authentication tested
- ✅ Power BI workspace access verified
- ✅ Monitoring and alerting configured

## 📈 Enterprise Benefits

- **🔒 Security:** Multi-layer security with OAuth, JWT, and API Management
- **📊 Analytics:** Complete API usage and performance monitoring
- **⚡ Scale:** Handle enterprise-level traffic and concurrent users
- **🛡️ Compliance:** Audit logging for security and compliance requirements
- **🔧 Management:** Centralized API management and policy enforcement

## 🤝 Contributing

This is an enterprise production system. For modifications:
1. Test changes locally with `mcp_server.py`
2. Update security policies if needed
3. Test with API Management before production
4. Update documentation for any new features

## 📄 License

Enterprise deployment for internal use. Ensure compliance with:
- Microsoft Power BI licensing terms
- Claude.ai Enterprise agreement terms
- Azure service agreements

---

**🎉 Ready to connect your Power BI data to Claude.ai Enterprise?**  
Start with the **[Complete Setup Guide](COMPLETE_SETUP_GUIDE.md)** for step-by-step instructions!