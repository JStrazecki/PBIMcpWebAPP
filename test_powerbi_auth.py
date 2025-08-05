"""
Test Power BI authentication and API access
"""

import os
import requests
import json
from datetime import datetime

# Get credentials from environment
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET', '')
TENANT_ID = os.environ.get('AZURE_TENANT_ID', '')

print(f"Testing Power BI Authentication")
print(f"================================")
print(f"CLIENT_ID: {CLIENT_ID[:8]}..." if CLIENT_ID else "CLIENT_ID: Not set")
print(f"CLIENT_SECRET: {'*' * 8}" if CLIENT_SECRET else "CLIENT_SECRET: Not set")
print(f"TENANT_ID: {TENANT_ID}")
print()

# Step 1: Get token
print("Step 1: Acquiring token...")
token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
token_data = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'scope': 'https://analysis.windows.net/powerbi/api/.default',
    'grant_type': 'client_credentials'
}

try:
    response = requests.post(token_url, data=token_data, timeout=30)
    print(f"Token response status: {response.status_code}")
    
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info.get('access_token')
        print(f"✓ Token acquired successfully")
        print(f"  Token length: {len(access_token)}")
        print(f"  Expires in: {token_info.get('expires_in')} seconds")
        
        # Decode token to check claims (without validation)
        import base64
        token_parts = access_token.split('.')
        if len(token_parts) >= 2:
            # Add padding if needed
            payload = token_parts[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            claims = json.loads(decoded)
            print(f"\nToken claims:")
            print(f"  App ID: {claims.get('appid', 'N/A')}")
            print(f"  Tenant: {claims.get('tid', 'N/A')}")
            print(f"  Roles: {claims.get('roles', [])}")
            print(f"  Scopes: {claims.get('scp', 'N/A')}")
    else:
        print(f"✗ Failed to get token: {response.text}")
        exit(1)
        
except Exception as e:
    print(f"✗ Error getting token: {e}")
    exit(1)

print("\nStep 2: Testing API access...")
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Test 1: List workspaces
print("\nTest 1: List workspaces")
try:
    url = "https://api.powerbi.com/v1.0/myorg/groups"
    response = requests.get(url, headers=headers, timeout=30)
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        workspaces = response.json().get('value', [])
        print(f"✓ Found {len(workspaces)} workspaces")
        for ws in workspaces[:2]:
            print(f"  - {ws['name']} ({ws['id']})")
    else:
        print(f"✗ Failed: {response.text[:200]}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Get specific workspace
workspace_id = "6d40d0dc-7eb0-44a1-9979-0de51f73c71c"  # Onetribe Demo
print(f"\nTest 2: Get workspace details")
try:
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
    response = requests.get(url, headers=headers, timeout=30)
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        ws = response.json()
        print(f"✓ Workspace: {ws['name']}")
        print(f"  Type: {ws.get('type', 'N/A')}")
        print(f"  State: {ws.get('state', 'N/A')}")
    else:
        print(f"✗ Failed: {response.text[:200]}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: List datasets in workspace
print(f"\nTest 3: List datasets in workspace")
try:
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    response = requests.get(url, headers=headers, timeout=30)
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        datasets = response.json().get('value', [])
        print(f"✓ Found {len(datasets)} datasets")
        for ds in datasets:
            print(f"  - {ds['name']} ({ds['id']})")
            dataset_id = ds['id']
    else:
        print(f"✗ Failed: {response.text[:200]}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Try to execute a simple query
if 'dataset_id' in locals():
    print(f"\nTest 4: Execute DAX query on dataset {dataset_id}")
    try:
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
        payload = {
            "queries": [{
                "query": "EVALUATE ROW(\"Test\", 1)"
            }],
            "serializerSettings": {
                "includeNulls": True
            }
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ Query executed successfully")
            result = response.json()
            print(f"  Results: {json.dumps(result, indent=2)[:200]}...")
        else:
            print(f"✗ Failed: {response.text[:500]}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error = error_data['error']
                    print(f"\nError details:")
                    print(f"  Code: {error.get('code', 'N/A')}")
                    if 'pbi.error' in error:
                        pbi_error = error['pbi.error']
                        print(f"  PBI Code: {pbi_error.get('code', 'N/A')}")
                        if 'details' in pbi_error:
                            for detail in pbi_error['details']:
                                print(f"  Detail: {detail.get('detail', {}).get('value', 'N/A')}")
            except:
                pass
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "="*50)
print("Testing complete")