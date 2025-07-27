#!/usr/bin/env python3
"""
Simple Environment Variables Test Script
Tests all required environment variables for Power BI MCP Finance Server
"""

import os
import sys
from datetime import datetime
from pathlib import Path

def check_env_var(var_name, description, required=True, sensitive=False):
    """Check if environment variable is set"""
    value = os.environ.get(var_name)
    
    if value:
        if sensitive and len(value) > 8:
            display_value = f"{value[:4]}***{value[-4:]}"
        elif sensitive:
            display_value = "***"
        else:
            display_value = value[:50] + "..." if len(value) > 50 else value
        
        status = "SET"
        print(f"{status:8} {var_name:25} {display_value}")
        return True
    else:
        status = "MISSING" if required else "OPTIONAL"
        print(f"{status:8} {var_name:25} {description}")
        return False

def main():
    """Run environment test"""
    print("POWER BI MCP FINANCE SERVER - ENVIRONMENT TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Check for .env file
    if Path('.env').exists():
        print("Found .env file")
        try:
            from dotenv import load_dotenv
            load_dotenv('.env')
            print("Loaded .env file")
        except ImportError:
            print("python-dotenv not installed - .env file ignored")
    else:
        print("No .env file found")
    
    print("\nPOWER BI AUTHENTICATION")
    print("-" * 30)
    
    # Power BI credentials
    has_manual_token = check_env_var("POWERBI_TOKEN", "Manual Power BI bearer token", required=False, sensitive=True)
    has_client_id = check_env_var("POWERBI_CLIENT_ID", "Power BI app client ID", required=True)
    has_client_secret = check_env_var("POWERBI_CLIENT_SECRET", "Power BI app client secret", required=True, sensitive=True)
    has_tenant_id = check_env_var("POWERBI_TENANT_ID", "Azure tenant ID", required=True)
    
    print("\nWEB AUTHENTICATION")
    print("-" * 30)
    
    auth_enabled = os.environ.get('AUTH_ENABLED', '').lower() in ('true', '1', 'yes')
    print(f"{'SET':8} {'AUTH_ENABLED':25} {'true' if auth_enabled else 'false'}")
    
    if auth_enabled:
        check_env_var("AZURE_CLIENT_ID", "Azure AD app client ID", required=True)
        check_env_var("AZURE_CLIENT_SECRET", "Azure AD app client secret", required=True, sensitive=True)
        check_env_var("AZURE_TENANT_ID", "Azure tenant ID", required=True)
        check_env_var("AZURE_REDIRECT_URI", "OAuth redirect URI", required=False)
    
    print("\nSECURITY")
    print("-" * 30)
    check_env_var("FLASK_SECRET_KEY", "Flask session secret key", required=True, sensitive=True)
    
    print("\nSERVER CONFIGURATION")
    print("-" * 30)
    check_env_var("PORT", "Server port", required=False)
    check_env_var("LOG_LEVEL", "Logging level", required=False)
    check_env_var("DEBUG", "Debug mode", required=False)
    
    print("\nAZURE DEPLOYMENT")
    print("-" * 30)
    website_hostname = check_env_var("WEBSITE_HOSTNAME", "Azure Web App hostname", required=False)
    check_env_var("DEPLOYMENT_ENV", "Deployment environment", required=False)
    
    # Summary
    print("\nSUMMARY")
    print("-" * 30)
    
    has_oauth = has_client_id and has_client_secret and has_tenant_id
    
    if has_manual_token:
        print("Power BI auth: Manual token available")
        if has_oauth:
            print("OAuth2: Also configured as fallback")
    elif has_oauth:
        print("Power BI auth: OAuth2 configured")
    else:
        print("Power BI auth: NOT CONFIGURED")
        print("\nTo fix:")
        print("1. Copy .env.template to .env")
        print("2. Fill in POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET, POWERBI_TENANT_ID")
        print("3. Or set POWERBI_TOKEN for manual token")
        return False
    
    if not check_env_var("FLASK_SECRET_KEY", "", required=False):
        print("Flask secret: MISSING - generate a random string")
        return False
    
    if website_hostname:
        print("Environment: Azure Web App")
    else:
        print("Environment: Local/Development")
    
    print("\nConfiguration appears valid!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)