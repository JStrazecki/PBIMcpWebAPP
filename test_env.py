#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment Variables Test Script
Tests all required environment variables for Power BI MCP Finance Server
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Set UTF-8 encoding for output
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    if Path('.env').exists():
        load_dotenv('.env')
        print("✓ Loaded .env file")
    else:
        print("i No .env file found - checking system environment variables")
except ImportError:
    print("i python-dotenv not installed - checking system environment variables only")

def check_env_var(var_name, description, required=True, sensitive=False):
    """Check if environment variable is set and optionally display its value"""
    value = os.environ.get(var_name)
    
    if value:
        if sensitive and len(value) > 8:
            display_value = f"{value[:4]}***{value[-4:]}"
        elif sensitive:
            display_value = "***"
        else:
            display_value = value[:50] + "..." if len(value) > 50 else value
        
        status = "✓ SET"
        print(f"{status:8} {var_name:25} {display_value}")
        return True
    else:
        status = "✗ MISSING" if required else "i OPTIONAL"
        print(f"{status:8} {var_name:25} {description}")
        return False

def test_power_bi_auth():
    """Test Power BI authentication configuration"""
    print("\nPOWER BI AUTHENTICATION")
    print("=" * 50)
    
    # Check for manual token first
    has_manual_token = check_env_var("POWERBI_TOKEN", "Manual Power BI bearer token", required=False, sensitive=True)
    
    # Check OAuth credentials
    has_client_id = check_env_var("POWERBI_CLIENT_ID", "Power BI app client ID", required=True)
    has_client_secret = check_env_var("POWERBI_CLIENT_SECRET", "Power BI app client secret", required=True, sensitive=True)
    has_tenant_id = check_env_var("POWERBI_TENANT_ID", "Azure tenant ID", required=True)
    
    has_oauth = has_client_id and has_client_secret and has_tenant_id
    
    if has_manual_token:
        print("✓ Power BI authentication: Manual token available")
        if has_oauth:
            print("✓ OAuth2 also configured as fallback")
        else:
            print("! OAuth2 not configured - only manual token available")
        return True
    elif has_oauth:
        print("✓ Power BI authentication: OAuth2 configured")
        return True
    else:
        print("✗ Power BI authentication: Not configured")
        return False

def test_web_auth():
    """Test web authentication configuration"""
    print("\n🌐 WEB AUTHENTICATION")
    print("=" * 50)
    
    auth_enabled = os.environ.get('AUTH_ENABLED', '').lower() in ('true', '1', 'yes')
    print(f"{'✅ ENABLED' if auth_enabled else 'ℹ️  DISABLED':8} AUTH_ENABLED         {'true' if auth_enabled else 'false'}")
    
    if not auth_enabled:
        print("ℹ️  Web authentication disabled - skipping Azure AD checks")
        return True
    
    has_azure_client_id = check_env_var("AZURE_CLIENT_ID", "Azure AD app client ID", required=True)
    has_azure_client_secret = check_env_var("AZURE_CLIENT_SECRET", "Azure AD app client secret", required=True, sensitive=True)
    has_azure_tenant_id = check_env_var("AZURE_TENANT_ID", "Azure tenant ID", required=True)
    check_env_var("AZURE_REDIRECT_URI", "OAuth redirect URI", required=False)
    
    return has_azure_client_id and has_azure_client_secret and has_azure_tenant_id

def test_security():
    """Test security configuration"""
    print("\n🔒 SECURITY")
    print("=" * 50)
    
    return check_env_var("FLASK_SECRET_KEY", "Flask session secret key", required=True, sensitive=True)

def test_server_config():
    """Test server configuration"""
    print("\n🌐 SERVER CONFIGURATION")
    print("=" * 50)
    
    check_env_var("PORT", "Server port", required=False)
    check_env_var("AUTH_PORT", "Authentication server port", required=False)
    check_env_var("LOG_LEVEL", "Logging level", required=False)
    check_env_var("DEBUG", "Debug mode", required=False)
    
    return True

def test_azure_deployment():
    """Test Azure deployment configuration"""
    print("\n☁️  AZURE DEPLOYMENT")
    print("=" * 50)
    
    website_hostname = check_env_var("WEBSITE_HOSTNAME", "Azure Web App hostname", required=False)
    check_env_var("DEPLOYMENT_ENV", "Deployment environment", required=False)
    
    if website_hostname:
        print("✅ Running on Azure Web App")
    else:
        print("ℹ️  Running locally or on non-Azure environment")
    
    return True

def test_mcp_config():
    """Test MCP server configuration"""
    print("\n🎯 MCP SERVER")
    print("=" * 50)
    
    check_env_var("SHARED_DIR", "Shared directory path", required=False)
    check_env_var("CONVERSATION_TRACKING", "Conversation tracking", required=False)
    
    return True

def test_power_bi_connection():
    """Test actual Power BI connection"""
    print("\n📊 POWER BI CONNECTION TEST")
    print("=" * 50)
    
    try:
        # Try to import and test the auth manager
        sys.path.append(str(Path(__file__).parent))
        from pbi_mcp_finance.auth.oauth_manager import get_token_manager, get_powerbi_token
        
        print("✅ Power BI modules imported successfully")
        
        # Test token retrieval
        token = get_powerbi_token()
        if token:
            print("✅ Power BI token retrieved successfully")
            
            # Get token info
            token_manager = get_token_manager()
            token_info = token_manager.get_token_info()
            print(f"ℹ️  Token status: {token_info.get('status', 'unknown')}")
            
            if token_info.get('using_manual_token'):
                print("ℹ️  Using manual bearer token")
            else:
                print("ℹ️  Using OAuth2 token")
                
            return True
        else:
            print("❌ Failed to retrieve Power BI token")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import Power BI modules: {e}")
        return False
    except Exception as e:
        print(f"❌ Power BI connection test failed: {e}")
        return False

def main():
    """Run all environment tests"""
    print("🧪 POWER BI MCP FINANCE SERVER - ENVIRONMENT TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Run all tests
    tests = [
        ("Power BI Authentication", test_power_bi_auth),
        ("Web Authentication", test_web_auth),
        ("Security", test_security),
        ("Server Configuration", test_server_config),
        ("Azure Deployment", test_azure_deployment),
        ("MCP Configuration", test_mcp_config),
        ("Power BI Connection", test_power_bi_connection)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your environment is properly configured.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the configuration above.")
        print("\n💡 Next steps:")
        print("1. Copy .env.template to .env")
        print("2. Fill in the missing values")
        print("3. Run this script again")
        sys.exit(1)

if __name__ == "__main__":
    main()