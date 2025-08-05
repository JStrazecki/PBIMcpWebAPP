"""
Power BI Authentication Diagnostics
This script helps diagnose Power BI authentication and permission issues
"""

import os
import sys
import requests
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pbi_mcp_finance.auth.oauth_manager import get_powerbi_token, get_token_manager
from pbi_mcp_finance.config.settings import settings


def print_section(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)


def check_environment_variables():
    """Check if all required environment variables are set"""
    print_section("Environment Variables Check")
    
    vars_to_check = {
        "POWERBI_CLIENT_ID": os.environ.get("POWERBI_CLIENT_ID"),
        "POWERBI_CLIENT_SECRET": os.environ.get("POWERBI_CLIENT_SECRET", "***SET***" if os.environ.get("POWERBI_CLIENT_SECRET") else None),
        "POWERBI_TENANT_ID": os.environ.get("POWERBI_TENANT_ID"),
        "POWERBI_WORKSPACE": os.environ.get("POWERBI_WORKSPACE"),
        "POWERBI_WORKSPACE_ID": os.environ.get("POWERBI_WORKSPACE_ID"),
        "POWERBI_DATASET": os.environ.get("POWERBI_DATASET"),
        "POWERBI_TOKEN":  os.environ.get("POWERBI_TOKEN"),
    }
    
    for var, value in vars_to_check.items():
        status = "[OK]" if value else "[MISSING]"
        print(f"{status} {var}: {value if value else 'NOT SET'}")
    
    return all([
        os.environ.get("POWERBI_CLIENT_ID"),
        os.environ.get("POWERBI_CLIENT_SECRET"),
        os.environ.get("POWERBI_TENANT_ID")
    ])


def test_token_acquisition():
    """Test if we can acquire a valid token"""
    print_section("Token Acquisition Test")
    
    try:
        token = get_powerbi_token()
        if token:
            print("[OK] Successfully acquired Power BI token")
            
            # Get token info
            token_info = get_token_manager().get_token_info()
            print(f"  Token Type: {token_info.get('type', 'Unknown')}")
            print(f"  Status: {token_info.get('status', 'Unknown')}")
            if token_info.get('expires_at') and token_info['expires_at'] != 'Never (manual token)':
                print(f"  Expires: {token_info['expires_at']}")
            
            return token
        else:
            print("[FAILED] Failed to acquire Power BI token")
            return None
    except Exception as e:
        print(f"[ERROR] Error acquiring token: {e}")
        return None


def test_api_permissions(token):
    """Test various Power BI API endpoints to check permissions"""
    print_section("API Permissions Test")
    
    if not token:
        print("[ERROR] No token available for testing")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test endpoints
    tests = [
        {
            "name": "List Workspaces",
            "url": "https://api.powerbi.com/v1.0/myorg/groups",
            "method": "GET",
            "required_permission": "Workspace.Read.All"
        },
        {
            "name": "List All Datasets",
            "url": "https://api.powerbi.com/v1.0/myorg/datasets",
            "method": "GET",
            "required_permission": "Dataset.Read.All"
        }
    ]
    
    results = {}
    
    for test in tests:
        print(f"\nTesting: {test['name']}")
        print(f"Endpoint: {test['url']}")
        print(f"Required Permission: {test['required_permission']}")
        
        try:
            response = requests.request(
                method=test['method'],
                url=test['url'],
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"[OK] Success - Status: {response.status_code}")
                data = response.json()
                if 'value' in data:
                    print(f"  Found {len(data['value'])} items")
                results[test['name']] = True
            else:
                print(f"[FAILED] Failed - Status: {response.status_code}")
                print(f"  Raw API Response:")
                print(f"  {response.text}")
                print(f"  Response Headers: {dict(response.headers)}")
                results[test['name']] = False
                
        except Exception as e:
            print(f"[ERROR] Exception: {e}")
            results[test['name']] = False
    
    return results


def test_workspace_access(token):
    """Test access to specific workspaces and datasets"""
    print_section("Workspace and Dataset Access Test")
    
    if not token:
        print("[ERROR] No token available for testing")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # First, list workspaces
    try:
        response = requests.get(
            "https://api.powerbi.com/v1.0/myorg/groups",
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print("[ERROR] Cannot list workspaces")
            return
        
        workspaces = response.json().get('value', [])
        print(f"[OK] Found {len(workspaces)} workspaces")
        
        # Test each workspace
        for ws in workspaces[:3]:  # Test first 3 workspaces
            print(f"\n  Workspace: {ws['name']}")
            print(f"  ID: {ws['id']}")
            
            # Try to list datasets in workspace
            ds_response = requests.get(
                f"https://api.powerbi.com/v1.0/myorg/groups/{ws['id']}/datasets",
                headers=headers,
                timeout=30
            )
            
            if ds_response.status_code == 200:
                datasets = ds_response.json().get('value', [])
                print(f"  [OK] Can access datasets - Found {len(datasets)} datasets")
                
                # Test DAX query on first dataset
                if datasets:
                    ds = datasets[0]
                    print(f"    Testing DAX query on: {ds['name']}")
                    
                    query_data = {
                        "queries": [{"query": "EVALUATE {1}"}]
                    }
                    
                    query_response = requests.post(
                        f"https://api.powerbi.com/v1.0/myorg/groups/{ws['id']}/datasets/{ds['id']}/executeQueries",
                        headers=headers,
                        json=query_data,
                        timeout=30
                    )
                    
                    if query_response.status_code == 200:
                        print("    [OK] DAX query successful")
                    else:
                        print(f"    [FAILED] DAX query failed - Status: {query_response.status_code}")
                        print(f"    Raw API Response:")
                        print(f"    {query_response.text}")
                        print(f"    Request URL: {query_response.url}")
                        print(f"    Request Body: {json.dumps(query_data, indent=6)}")
            else:
                print(f"  [FAILED] Cannot access datasets - Status: {ds_response.status_code}")
                print(f"  Raw API Response: {ds_response.text}")
                
    except Exception as e:
        print(f"[ERROR] Error testing workspaces: {e}")


def provide_recommendations(oauth_configured, results):
    """Provide specific recommendations based on test results"""
    print_section("Recommendations")
    
    if not oauth_configured:
        print("1. Set up OAuth2 authentication:")
        print("   - Set POWERBI_CLIENT_ID environment variable")
        print("   - Set POWERBI_CLIENT_SECRET environment variable")
        print("   - Set POWERBI_TENANT_ID environment variable")
        print()
    
    if results and not results.get("List All Datasets", True):
        print("2. Add Dataset.Read.All permission in Azure AD:")
        print("   a. Go to Azure Portal > App registrations")
        print("   b. Select your app registration")
        print("   c. Go to API permissions")
        print("   d. Add permission > Power BI Service > Application permissions")
        print("   e. Select 'Dataset.Read.All'")
        print("   f. Grant admin consent")
        print()
    
    print("3. Enable service principals in Power BI Admin Portal:")
    print("   a. Go to Power BI Admin Portal > Tenant settings")
    print("   b. Enable 'Service principals can use Power BI APIs'")
    print("   c. Apply to specific security groups or entire organization")
    print()
    
    print("4. Add service principal to workspaces:")
    print("   a. Go to each Power BI workspace")
    print("   b. Click 'Access' or 'Manage access'")
    print("   c. Add your service principal with 'Member' role")
    print()
    
    print("5. For DAX query access (XMLA endpoint):")
    print("   a. Go to Power BI workspace settings")
    print("   b. Premium/Capacity settings")
    print("   c. Enable 'XMLA Endpoint' with 'Read' access")
    print("   d. Ensure dataset is in a Premium/PPU workspace")


def main():
    """Run all diagnostics"""
    print("Power BI Authentication Diagnostics")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check environment
    oauth_configured = check_environment_variables()
    
    # Test token
    token = test_token_acquisition()
    
    # Test API permissions
    results = {}
    if token:
        results = test_api_permissions(token)
        test_workspace_access(token)
    
    # Provide recommendations
    provide_recommendations(oauth_configured, results)
    
    print("\n" + "="*60)
    print("Diagnostics complete!")


if __name__ == "__main__":
    main()