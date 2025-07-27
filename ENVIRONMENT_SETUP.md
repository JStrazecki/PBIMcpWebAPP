# Environment Variables Setup

## 🔧 Local Development Setup

1. **Copy the template:**
   ```bash
   cp .env.template .env
   ```

2. **Fill in your existing Power BI values:**
   - `POWERBI_CLIENT_ID`
   - `POWERBI_CLIENT_SECRET` 
   - `POWERBI_TENANT_ID`

3. **For local testing without authentication:**
   ```bash
   # In your .env file
   AUTH_ENABLED=false
   ```

4. **For local testing with authentication:**
   - Follow the Azure AD setup in `.env.template`
   - Set `AUTH_ENABLED=true`
   - Use `http://localhost:8000/auth/callback` as redirect URI for local testing

## 🌐 Azure Web App Setup

**Don't upload your .env file to Azure!** Instead:

1. **Go to**: Azure Portal > Your Web App > Configuration > Application settings

2. **Add each variable individually:**
   - Click "New application setting"
   - Name: `AUTH_ENABLED`, Value: `true`
   - Name: `AZURE_CLIENT_ID`, Value: `your-actual-client-id`
   - Continue for all variables...

3. **Use production redirect URI:**
   ```
   AZURE_REDIRECT_URI=https://pbimcp.azurewebsites.net/auth/callback
   ```

## 🔑 Quick Variable Reference

| Variable | Where to Get It | Used For |
|----------|----------------|----------|
| `POWERBI_CLIENT_ID` | Your existing Power BI app | Power BI API access |
| `POWERBI_CLIENT_SECRET` | Your existing Power BI app | Power BI API access |
| `POWERBI_TENANT_ID` | Your existing Azure tenant | Power BI API access |
| `AZURE_CLIENT_ID` | New Azure AD app registration | Web authentication |
| `AZURE_CLIENT_SECRET` | New Azure AD app registration | Web authentication |
| `AZURE_TENANT_ID` | Same as POWERBI_TENANT_ID | Web authentication |
| `FLASK_SECRET_KEY` | Generate random string | Session security |

## 🚨 Security Notes

- ✅ `.env` files are in `.gitignore` - won't be committed
- ✅ Use different redirect URIs for local vs production
- ✅ Generate strong `FLASK_SECRET_KEY`
- ✅ Keep Power BI and Azure AD registrations separate