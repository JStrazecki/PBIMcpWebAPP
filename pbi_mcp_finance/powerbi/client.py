"""
Power BI API client for financial data access
"""

import time
import requests
from typing import Dict, Any, Optional, List

from ..config.settings import settings
from ..auth.oauth_manager import get_powerbi_token, get_token_manager
from ..auth import get_auth_token
from ..utils.logging import powerbi_logger
from ..utils.exceptions import (
    PowerBIError, AuthenticationError, WorkspaceNotFoundError, 
    DatasetNotFoundError, DAXQueryError
)
from .permissions_handler import PermissionsHandler


class PowerBIClient:
    """Power BI API client with comprehensive error handling"""
    
    def __init__(self):
        self.api_base_url = settings.powerbi_api_base_url
        self.fabric_api_base_url = settings.fabric_api_base_url
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers with fresh token"""
        # Try Microsoft OAuth authentication first (if authenticated via web)
        oauth_token = get_auth_token()
        if oauth_token:
            powerbi_logger.debug("Using Microsoft OAuth token for Power BI API")
            return {
                "Authorization": f"Bearer {oauth_token}",
                "Content-Type": "application/json"
            }
        
        # Fall back to Power BI specific token (existing flow)
        token = get_powerbi_token()
        if not token:
            powerbi_logger.warning("No valid Power BI token available")
            raise AuthenticationError("No valid Power BI token available")
        
        powerbi_logger.debug("Using Power BI service token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def make_request(self, url: str, method: str = "GET", 
                    data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request to Power BI API with enhanced monitoring"""
        start_time = time.time()
        headers = self.get_auth_headers()
        
        error_message = None
        dax_query = None
        
        # Extract DAX query if present
        if data and "queries" in data:
            dax_query = data["queries"][0].get("query", "") if data["queries"] else ""
        
        try:
            powerbi_logger.debug(f"Making {method} request to {url}")
            
            # First attempt
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=30)
            
            # If token expired, try to refresh and retry once
            if response.status_code == 401 or (response.status_code == 403 and "TokenExpired" in response.text):
                powerbi_logger.info("Token expired, attempting refresh...")
                
                # Invalidate current token and get fresh one
                get_token_manager().invalidate_token()
                headers = self.get_auth_headers()
                
                # Retry the request with fresh token
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=30)
                else:
                    response = requests.post(url, headers=headers, json=data, timeout=30)
            
            # Calculate metrics
            elapsed_ms = (time.time() - start_time) * 1000
            
            powerbi_logger.debug(f"Request completed in {elapsed_ms:.0f}ms with status {response.status_code}")
            
            if not response.ok:
                error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                powerbi_logger.error(error_message)
                
                # Classify errors with enhanced diagnostics
                if response.status_code == 401:
                    raise AuthenticationError(error_message)
                elif response.status_code == 404:
                    raise PowerBIError(error_message)
                elif response.status_code == 403:
                    # Handle permission errors specially
                    if "API is not accessible for application" in response.text:
                        diagnostic = PermissionsHandler.analyze_error(response.text, 403)
                        error_msg = (
                            f"Power BI API permissions not configured. "
                            f"The service principal doesn't have the required Power BI API permissions. "
                            f"Required: {', '.join(diagnostic['permissions_needed'])}"
                        )
                        raise PowerBIError(error_msg)
                    else:
                        raise PowerBIError(error_message)
                else:
                    raise PowerBIError(error_message)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            elapsed_ms = (time.time() - start_time) * 1000
            error_message = str(e)
            powerbi_logger.error(f"Request failed after {elapsed_ms:.0f}ms: {error_message}")
            raise PowerBIError(f"API request failed: {error_message}")
    
    def get_workspaces(self) -> List[Dict[str, Any]]:
        """Get list of Power BI workspaces"""
        try:
            result = self.make_request(f"{self.api_base_url}/groups")
            return result.get("value", [])
        except Exception as e:
            powerbi_logger.error(f"Failed to get workspaces: {e}")
            raise
    
    def get_workspace_by_name(self, workspace_name: str) -> Dict[str, Any]:
        """Get workspace by name"""
        if workspace_name is None:
            raise WorkspaceNotFoundError("Workspace name cannot be None")
        
        # Check if we have default workspace settings and they match
        default_workspace_name = settings.default_workspace_name
        default_workspace_id = settings.default_workspace_id
        
        if (default_workspace_name is not None and 
            default_workspace_id is not None and
            workspace_name.lower() == default_workspace_name.lower()):
            return {
                "id": default_workspace_id,
                "name": default_workspace_name
            }
        
        # Search through all available workspaces
        workspaces = self.get_workspaces()
        for ws in workspaces:
            # Safely handle None workspace names
            ws_name = ws.get('name')
            if ws_name is not None and ws_name.lower() == workspace_name.lower():
                return ws
        
        raise WorkspaceNotFoundError(f"Workspace '{workspace_name}' not found")
    
    def get_datasets(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get datasets in a workspace"""
        try:
            result = self.make_request(f"{self.api_base_url}/groups/{workspace_id}/datasets")
            return result.get("value", [])
        except Exception as e:
            powerbi_logger.error(f"Failed to get datasets for workspace {workspace_id}: {e}")
            raise
    
    def get_dataset_by_name(self, workspace_id: str, dataset_name: str) -> Dict[str, Any]:
        """Get dataset by name in a workspace"""
        if dataset_name is None:
            raise DatasetNotFoundError("Dataset name cannot be None")
        
        datasets = self.get_datasets(workspace_id)
        for ds in datasets:
            # Safely handle None names
            ds_name = ds.get('name')
            if ds_name is not None and ds_name.lower() == dataset_name.lower():
                return ds
        
        raise DatasetNotFoundError(f"Dataset '{dataset_name}' not found")
    
    def execute_dax_query(self, workspace_id: str, dataset_id: str, 
                         dax_query: str) -> Dict[str, Any]:
        """Execute DAX query against a dataset"""
        try:
            data = {"queries": [{"query": dax_query}]}
            url = f"{self.api_base_url}/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
            
            powerbi_logger.debug(f"Executing DAX query: {dax_query[:100]}...")
            result = self.make_request(url, method="POST", data=data)
            
            # Validate result structure
            if "results" not in result:
                raise DAXQueryError("Invalid query response structure")
            
            return result
            
        except PowerBIError:
            raise
        except Exception as e:
            powerbi_logger.error(f"DAX query execution failed: {e}")
            raise DAXQueryError(f"Query execution failed: {e}")
    
    def get_model_definition(self, workspace_id: str, dataset_id: str) -> Dict[str, Any]:
        """Get semantic model definition"""
        try:
            url = f"{self.fabric_api_base_url}/workspaces/{workspace_id}/semanticModels/{dataset_id}/getDefinition"
            
            # This might be a long-running operation
            response = requests.post(url, headers=self.get_auth_headers(), timeout=30)
            
            # Handle long-running operation
            if response.status_code == 202:
                location = response.headers.get('Location')
                retry_after = int(response.headers.get('Retry-After', 30))
                return self._wait_for_operation(location, retry_after)
            elif response.ok:
                return response.json()
            else:
                raise PowerBIError(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            powerbi_logger.error(f"Failed to get model definition: {e}")
            raise PowerBIError(f"Model definition request failed: {e}")
    
    def _wait_for_operation(self, location_url: str, retry_seconds: int = 30) -> Dict[str, Any]:
        """Wait for long-running operations to complete"""
        headers = self.get_auth_headers()
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            time.sleep(retry_seconds)
            retry_count += 1
            
            try:
                response = requests.get(location_url, headers=headers, timeout=30)
                
                if response.ok:
                    data = response.json()
                    status = data.get('status', '')
                    
                    if status == 'Succeeded':
                        result_response = requests.get(f"{location_url}/result", headers=headers, timeout=30)
                        if result_response.ok:
                            return result_response.json()
                        else:
                            raise PowerBIError("Failed to get operation result")
                    elif status == 'Failed':
                        raise PowerBIError(data.get('error', 'Operation failed'))
                    else:
                        powerbi_logger.debug(f"Operation status: {status}, retrying in {retry_seconds}s")
                        continue
                else:
                    raise PowerBIError(f"Failed to check operation status: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                powerbi_logger.warning(f"Operation status check failed: {e}")
                continue
        
        raise PowerBIError("Operation timed out after maximum retries")


# Global client instance
_powerbi_client: Optional[PowerBIClient] = None


def get_powerbi_client() -> PowerBIClient:
    """Get the global Power BI client instance"""
    global _powerbi_client
    if _powerbi_client is None:
        _powerbi_client = PowerBIClient()
    return _powerbi_client