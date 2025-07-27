# Azure Web App Deployment Checklist

Use this checklist to ensure your Power BI MCP Finance Server is properly deployed to Azure Web App.

## 📋 Pre-Deployment Checklist

### ✅ Azure Resources Setup
- [ ] **Azure Web App Created**
  - Name: `pbimcp` (or your chosen name)
  - Runtime: Python 3.11
  - Operating System: Linux
  - App Service Plan: B1 or higher

### ✅ Power BI Service Setup
- [ ] **Power BI App Registration**
  - Azure AD app registered for Power BI API access
  - Client ID, Client Secret, and Tenant ID obtained
  - Service principal added to Power BI workspaces (if applicable)
  - **OR Manual Bearer Token obtained** (alternative to OAuth)

### ✅ Web Authentication Setup (Optional)
- [ ] **Azure AD App Registration for Web Auth**
  - Separate app registered for web interface authentication
  - Redirect URI configured: `https://your-app.azurewebsites.net/auth/callback`
  - API permissions granted: `User.Read`, `openid`, `profile`, `email`
  - Admin consent granted (if required)

### ✅ Code Preparation
- [ ] **Main Branch Ready**: All changes committed to `main` branch
- [ ] **Simplified Mode**: `main_simple.py` and `requirements_simple.txt` available
- [ ] **Startup Script**: `startup.sh` configured to auto-detect mode
- [ ] **GitHub Actions**: Updated workflow without artifacts
- [ ] **No Database Dependencies**: SQLite requirements removed

## 🔧 Azure Web App Configuration

### ✅ Critical Environment Variables 🚨
**App will not start without these! Add to Azure Portal > Configuration > Application settings:**

#### 🚨 Required Power BI Authentication (Choose ONE method)
**Method 1: OAuth2 (Recommended)**
- [ ] `POWERBI_CLIENT_ID=<your-powerbi-client-id>`
- [ ] `POWERBI_CLIENT_SECRET=<your-powerbi-client-secret>`
- [ ] `POWERBI_TENANT_ID=<your-azure-tenant-id>`

**Method 2: Manual Token (Alternative)**
- [ ] `POWERBI_TOKEN=<manual-bearer-token>`

#### 🚨 Required Security
- [ ] `FLASK_SECRET_KEY=<32-character-random-string>`
  Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### ✅ Optional Web Authentication Settings
#### Web Interface Authentication (if AUTH_ENABLED=true)
- [ ] `AUTH_ENABLED=true`
- [ ] `AZURE_CLIENT_ID=<web-auth-client-id>`
- [ ] `AZURE_CLIENT_SECRET=<web-auth-client-secret>`
- [ ] `AZURE_REDIRECT_URI=https://your-app.azurewebsites.net/auth/callback`

### ✅ Optional Configuration
- [ ] `LOG_LEVEL=INFO`
- [ ] `DEBUG=false`

### ✅ General Settings
- [ ] **Runtime stack**: Python 3.11
- [ ] **Startup Command**: `/home/site/wwwroot/startup.sh`
- [ ] **Always On**: Enabled (to prevent cold starts)

### ✅ Deployment Configuration
- [ ] **GitHub Actions (Recommended)**:
  - Connected to GitHub repository
  - Push to `main` branch triggers deployment
  - Build provider: GitHub Actions
  - **No artifacts** (fixed storage quota issue)

## 🚀 Deployment Steps

### ✅ GitHub Actions Deployment (Recommended)
- [ ] **Repository Connected**: GitHub Actions workflow active
- [ ] **Push to Main Branch**: `git push origin main`
- [ ] **Deployment Successful**: Check GitHub Actions logs
- [ ] **No Artifact Errors**: Storage quota issue resolved

### ✅ Alternative: Azure CLI Deployment
- [ ] **Azure CLI Method**:
  ```bash
  az webapp up --name your-app-name --resource-group your-rg --runtime "PYTHON:3.11"
  ```

### ✅ Alternative: ZIP Deployment
- [ ] **Files prepared** (exclude unnecessary files):
  ```bash
  zip -r deploy.zip . -x "venv/*" "*.git/*" "*.log" "__pycache__/*" "*.pyc" "AzureBotTest/*"
  ```

## 🧪 Post-Deployment Testing

### ✅ Basic Health Checks
- [ ] **Root Endpoint**: `https://your-app.azurewebsites.net/`
  - Expected: Service status with mode detection (simplified/full)

- [ ] **Health Check**: `https://your-app.azurewebsites.net/health`
  - Expected: Power BI auth status and environment info

### ✅ Power BI Integration
- [ ] **Power BI Status**: `https://your-app.azurewebsites.net/api/powerbi/workspaces`
  - Expected: Power BI authentication confirmation or error message

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