# Azure Web App Deployment Checklist

Use this checklist to ensure your Power BI MCP Finance Server is properly deployed to Azure Web App.

## 📋 Pre-Deployment Checklist

### ✅ Azure Resources Setup
- [ ] **Azure Web App Created**
  - Name: `pbimcp`
  - Runtime: Python 3.11
  - Operating System: Linux
  - App Service Plan: `linux-sqlbot` (B1 or higher)

- [ ] **Azure AD App Registration**
  - App registered in Azure Active Directory
  - Client ID, Client Secret, and Tenant ID obtained
  - Redirect URI configured: `https://pbimcp.azurewebsites.net/auth/callback`
  - API permissions granted: `User.Read`, `openid`, `profile`, `email`
  - Admin consent granted (if required)

- [ ] **Power BI Service Setup**
  - Power BI app registered (if using service principal)
  - Client ID and Client Secret for Power BI API access
  - Service principal added to Power BI workspaces (if applicable)

### ✅ Code Preparation
- [ ] **Branch Ready**: All changes committed to `feature/oauth-auth` branch
- [ ] **Dependencies Updated**: `requirements.txt` includes all necessary packages
- [ ] **Startup Script**: `startup.sh` is executable and configured
- [ ] **Configuration Files**: `web.config` created for Azure App Service
- [ ] **Database Disabled**: SQLite tracking disabled per requirements

## 🔧 Azure Web App Configuration

### ✅ Application Settings (Environment Variables)
Copy these to Azure Portal > Web App > Configuration > Application settings:

#### Authentication Configuration
- [ ] `AUTH_ENABLED=true`
- [ ] `FLASK_SECRET_KEY=<32-character-random-string>`
- [ ] `AUTH_PORT=8000`

#### Azure AD OAuth Settings
- [ ] `AZURE_CLIENT_ID=<your-azure-ad-client-id>`
- [ ] `AZURE_CLIENT_SECRET=<your-azure-ad-client-secret>`
- [ ] `AZURE_TENANT_ID=<your-azure-tenant-id>`
- [ ] `AZURE_REDIRECT_URI=https://pbimcp.azurewebsites.net/auth/callback`

#### Power BI API Settings
- [ ] `POWERBI_CLIENT_ID=<your-powerbi-client-id>`
- [ ] `POWERBI_CLIENT_SECRET=<your-powerbi-client-secret>`
- [ ] `POWERBI_TENANT_ID=<your-azure-tenant-id>`

#### Optional Power BI Manual Token (if preferred over service principal)
- [ ] `POWERBI_TOKEN=<manual-bearer-token>` (optional)

#### Application Platform Settings
- [ ] `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
- [ ] `WEBSITES_ENABLE_APP_SERVICE_STORAGE=false`
- [ ] `PYTHONPATH=/home/site/wwwroot`

### ✅ General Settings
- [ ] **Runtime stack**: Python 3.11
- [ ] **Startup Command**: `startup.sh`
- [ ] **Always On**: Enabled (to prevent cold starts)

### ✅ Deployment Configuration
- [ ] **Deployment method chosen**:
  - [ ] GitHub Actions (recommended)
  - [ ] ZIP deployment
  - [ ] FTP deployment

## 🚀 Deployment Steps

### ✅ GitHub Deployment (Recommended)
- [ ] **Connected to GitHub**:
  - Repository: `PbiMCPFinance`
  - Branch: `feature/oauth-auth`
  - Build provider: App Service build service

- [ ] **Deployment triggered and successful**
- [ ] **Build logs reviewed** (no errors)

### ✅ Alternative: Manual Deployment
- [ ] **Files prepared**:
  ```bash
  # Exclude unnecessary files
  zip -r deploy.zip . -x "venv/*" "*.git/*" "*.log" "__pycache__/*" "*.pyc" "shared/*"
  ```
- [ ] **Deployed via Azure CLI**:
  ```bash
  az webapp deploy --resource-group <your-resource-group> --name pbimcp --src-path deploy.zip
  ```

## 🧪 Post-Deployment Testing

### ✅ Health Checks
- [ ] **Basic Health Check**: `https://pbimcp.azurewebsites.net/`
  - Expected: `{"status": "healthy", "service": "Power BI MCP Finance Server", ...}`

- [ ] **Detailed Health Check**: `https://pbimcp.azurewebsites.net/health`
  - Expected: PowerBI auth status and OAuth configuration

- [ ] **Authentication Status**: `https://pbimcp.azurewebsites.net/auth/status`
  - Expected: `{"authenticated": false}` (before login)

### ✅ Authentication Flow
- [ ] **Login Endpoint**: `https://pbimcp.azurewebsites.net/auth/login`
  - Redirects to Microsoft login
  - Successful authentication redirects back
  - Success page displays correctly

- [ ] **Post-Login Status**: `https://pbimcp.azurewebsites.net/auth/status`
  - Expected: `{"authenticated": true, "user": {...}}`

- [ ] **Logout Endpoint**: `https://pbimcp.azurewebsites.net/auth/logout`
  - Clears session successfully

### ✅ Application Logs
- [ ] **Review startup logs**:
  ```bash
  az webapp log tail --name pbimcp --resource-group <your-resource-group>
  ```
- [ ] **No critical errors in logs**
- [ ] **Authentication configuration messages correct**
- [ ] **Power BI token validation successful**

### ✅ Power BI Integration
- [ ] **Power BI token working** (check logs for authentication success)
- [ ] **API endpoints responding** (if accessible)
- [ ] **No authentication errors in logs**

## 🔍 Monitoring Setup

### ✅ Application Insights (Recommended)
- [ ] **Application Insights enabled**
- [ ] **Custom telemetry configured** (optional)
- [ ] **Alerts configured** for errors and performance

### ✅ Log Analytics
- [ ] **Log streaming working**: Monitor real-time logs
- [ ] **Historical logs accessible**: Download and review
- [ ] **Error tracking setup**: Alerts for critical errors

## 🛡️ Security Verification

### ✅ HTTPS and Security Headers
- [ ] **HTTPS enforced**: HTTP redirects to HTTPS
- [ ] **Security headers present**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000`

### ✅ Authentication Security
- [ ] **OAuth state validation working** (CSRF protection)
- [ ] **Session management secure** (proper expiration)
- [ ] **Secrets not exposed** in logs or error messages

### ✅ Access Control
- [ ] **Authentication required for protected endpoints**
- [ ] **Unauthorized access properly blocked**
- [ ] **User information properly isolated**

## 🔧 Performance Optimization

### ✅ Basic Performance
- [ ] **Cold start time acceptable** (< 30 seconds)
- [ ] **Response times reasonable** (< 5 seconds for health checks)
- [ ] **Memory usage within limits** (< 512MB for B1 plan)

### ✅ Advanced Performance (Optional)
- [ ] **CDN configured** (for static assets if any)
- [ ] **Connection pooling optimized**
- [ ] **Gunicorn workers tuned** based on traffic

## 📞 Troubleshooting Checklist

### ✅ Common Issues Resolution
- [ ] **Module import errors**: PYTHONPATH set correctly
- [ ] **OAuth redirect mismatch**: URLs match exactly in Azure AD
- [ ] **Database lock issues**: SQLite usage disabled
- [ ] **Port binding issues**: Using Azure-provided PORT variable

### ✅ Debugging Tools Ready
- [ ] **Log access configured**: Can stream and download logs
- [ ] **SSH access enabled** (if needed for debugging)
- [ ] **Deployment slots configured** (for staging/production)

## ✅ Documentation and Handover

### ✅ Documentation Complete
- [ ] **Environment variables documented**
- [ ] **Deployment process documented**
- [ ] **Troubleshooting guide available**
- [ ] **Monitoring and alerting documented**

### ✅ Team Knowledge Transfer
- [ ] **Azure Portal access granted** to relevant team members
- [ ] **Azure AD app registration access** provided
- [ ] **Power BI workspace permissions** configured
- [ ] **Emergency procedures documented**

## 🎯 Go-Live Checklist

### ✅ Final Verification
- [ ] **All tests passing**
- [ ] **Performance acceptable**
- [ ] **Security review complete**
- [ ] **Monitoring active**
- [ ] **Backup/recovery plan in place**

### ✅ Communication
- [ ] **Stakeholders notified** of go-live
- [ ] **Support contacts provided**
- [ ] **Known issues communicated**
- [ ] **Rollback plan prepared**

---

## 🚨 Emergency Contacts

- **Azure Support**: Submit ticket in Azure Portal
- **Power BI Support**: https://powerbi.microsoft.com/support/
- **Application Owner**: [Your contact information]
- **Technical Lead**: [Technical contact information]

## 📝 Deployment Notes

**Deployment Date**: ________________

**Deployed By**: ____________________

**Version**: _______________________

**Notes**: 
```
[Add any specific notes about this deployment]
```

---

**✅ Deployment Complete**: All checklist items verified and application is live!