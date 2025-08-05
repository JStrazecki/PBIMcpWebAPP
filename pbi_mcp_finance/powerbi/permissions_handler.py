"""
Power BI Permissions Handler
Handles permission errors and provides detailed diagnostics
"""

import json
from typing import Dict, Any, Optional, Tuple
from ..utils.logging import powerbi_logger


class PermissionsHandler:
    """Handle Power BI API permission errors with detailed diagnostics"""
    
    # Known error patterns and their solutions
    ERROR_PATTERNS = {
        "API is not accessible for application": {
            "error_type": "SERVICE_PRINCIPAL_API_ACCESS",
            "permissions_needed": ["Dataset.Read.All"],
            "solutions": [
                "Add Power BI Service API permissions (Dataset.Read.All) in Azure AD",
                "Grant admin consent for the permissions",
                "Enable 'Service principals can use Power BI APIs' in Power BI Admin Portal",
                "Add service principal to workspace with Member role"
            ]
        },
        "Failed to open the MSOLAP connection": {
            "error_type": "XMLA_ENDPOINT_ACCESS",
            "permissions_needed": ["Workspace Member access", "XMLA Endpoint Read"],
            "solutions": [
                "Add service principal as Member (not just Viewer) to the workspace",
                "Enable XMLA endpoint read access in workspace settings (Premium/PPU required)",
                "Ensure dataset is refreshed and accessible",
                "Check if dataset security (RLS) is blocking access"
            ]
        },
        "TokenExpired": {
            "error_type": "TOKEN_EXPIRED",
            "permissions_needed": [],
            "solutions": [
                "Token has expired - authentication will refresh automatically",
                "If using manual token, update POWERBI_TOKEN environment variable"
            ]
        },
        "Unauthorized": {
            "error_type": "AUTHENTICATION_FAILED",
            "permissions_needed": [],
            "solutions": [
                "Verify POWERBI_CLIENT_ID is correct",
                "Verify POWERBI_CLIENT_SECRET is correct",
                "Verify POWERBI_TENANT_ID is correct",
                "Check if service principal is active in Azure AD"
            ]
        }
    }
    
    @classmethod
    def analyze_error(cls, error_message: str, status_code: int, 
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze an error and provide detailed diagnostics
        
        Args:
            error_message: The error message from Power BI API
            status_code: HTTP status code
            context: Additional context (workspace_id, dataset_id, etc.)
        
        Returns:
            Diagnostic information with solutions
        """
        # Identify error pattern
        error_info = None
        for pattern, info in cls.ERROR_PATTERNS.items():
            if pattern in error_message:
                error_info = info.copy()
                break
        
        # Default error info if pattern not found
        if not error_info:
            error_info = {
                "error_type": "UNKNOWN_ERROR",
                "permissions_needed": [],
                "solutions": [
                    "Check Power BI Admin Portal for service principal settings",
                    "Verify workspace access permissions",
                    "Check Azure AD app registration configuration"
                ]
            }
        
        # Build diagnostic response
        diagnostic = {
            "error": error_info["error_type"],
            "status_code": status_code,
            "message": cls._sanitize_error_message(error_message),
            "permissions_needed": error_info["permissions_needed"],
            "solutions": error_info["solutions"],
            "context": context or {}
        }
        
        # Add specific recommendations based on status code
        if status_code == 403:
            diagnostic["additional_info"] = "403 Forbidden - Service principal lacks required permissions"
        elif status_code == 401:
            diagnostic["additional_info"] = "401 Unauthorized - Authentication failed or token expired"
        elif status_code == 400 and "DatasetExecuteQueriesError" in error_message:
            diagnostic["additional_info"] = "Dataset query failed - Check XMLA endpoint and workspace permissions"
        
        return diagnostic
    
    @classmethod
    def _sanitize_error_message(cls, error_message: str) -> str:
        """Sanitize error message for display"""
        # Remove excessive whitespace
        error_message = ' '.join(error_message.split())
        
        # Truncate very long messages
        if len(error_message) > 500:
            error_message = error_message[:500] + "..."
        
        return error_message
    
    @classmethod
    def format_error_response(cls, diagnostic: Dict[str, Any]) -> str:
        """Format diagnostic information for user display"""
        lines = [
            f"Power BI API Error: {diagnostic['error']}",
            f"Status Code: {diagnostic['status_code']}",
            "",
            "Error Details:",
            diagnostic['message'],
            ""
        ]
        
        if diagnostic.get('additional_info'):
            lines.extend([
                "Additional Information:",
                diagnostic['additional_info'],
                ""
            ])
        
        if diagnostic['permissions_needed']:
            lines.extend([
                "Required Permissions:",
                *[f"  • {perm}" for perm in diagnostic['permissions_needed']],
                ""
            ])
        
        if diagnostic['solutions']:
            lines.extend([
                "Troubleshooting Steps:",
                *[f"  {i+1}. {solution}" for i, solution in enumerate(diagnostic['solutions'])],
                ""
            ])
        
        if diagnostic.get('context'):
            ctx = diagnostic['context']
            if ctx.get('workspace_id'):
                lines.append(f"Workspace ID: {ctx['workspace_id']}")
            if ctx.get('dataset_id'):
                lines.append(f"Dataset ID: {ctx['dataset_id']}")
        
        return '\n'.join(lines)
    
    @classmethod
    def check_permissions_status(cls, client) -> Dict[str, Any]:
        """
        Check current permissions status by testing various endpoints
        
        Returns:
            Dictionary with permission check results
        """
        results = {
            "can_list_workspaces": False,
            "can_list_all_datasets": False,
            "can_query_datasets": False,
            "errors": []
        }
        
        # Test workspace access
        try:
            workspaces = client.get_workspaces()
            results["can_list_workspaces"] = True
            results["workspace_count"] = len(workspaces)
        except Exception as e:
            results["errors"].append(f"Workspace access: {str(e)}")
        
        # Test dataset listing (requires Dataset.Read.All)
        try:
            response = client.make_request(f"{client.api_base_url}/datasets")
            results["can_list_all_datasets"] = True
        except Exception as e:
            results["errors"].append(f"Dataset listing: {str(e)}")
        
        return results


def handle_powerbi_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Handle Power BI errors with detailed diagnostics
    
    Args:
        error: The exception that occurred
        context: Additional context information
        
    Returns:
        Formatted error message with diagnostics
    """
    error_message = str(error)
    status_code = getattr(error, 'status_code', 500)
    
    # Try to extract more details from the error
    if hasattr(error, 'response'):
        try:
            error_details = error.response.json()
            if 'error' in error_details:
                error_message = json.dumps(error_details['error'])
        except:
            error_message = error.response.text
    
    # Analyze the error
    diagnostic = PermissionsHandler.analyze_error(error_message, status_code, context)
    
    # Log the error
    powerbi_logger.error(f"Power BI API error: {diagnostic['error']} - {error_message}")
    
    # Return formatted response
    return PermissionsHandler.format_error_response(diagnostic)