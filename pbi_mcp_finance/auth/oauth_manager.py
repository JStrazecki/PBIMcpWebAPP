"""
OAuth2 Token Manager for Power BI Authentication
Refactored from oauth2_token_manager.py with improved architecture
"""

import os
import requests
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from ..config.settings import settings
from ..utils.logging import auth_logger
from ..utils.exceptions import AuthenticationError, TokenExpiredError
from .token_storage import TokenStorage


class PowerBITokenManager:
    """
    Manages OAuth2 tokens for Power BI API access with automatic refresh
    """
    
    def __init__(self, client_id: Optional[str] = None, 
                 client_secret: Optional[str] = None, 
                 tenant_id: Optional[str] = None):
        """
        Initialize the token manager
        
        Args:
            client_id: Azure AD Application (client) ID
            client_secret: Azure AD Application secret
            tenant_id: Azure AD Tenant ID
        """
        # OAuth2 configuration - use provided values or settings
        self.client_id = client_id or settings.powerbi_client_id
        self.client_secret = client_secret or settings.powerbi_client_secret
        self.tenant_id = tenant_id or settings.powerbi_tenant_id
        
        # OAuth2 URLs and scopes
        self.scope = settings.oauth_scope
        self.token_url = settings.oauth_token_url
        
        # Token state
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.refresh_token: Optional[str] = None
        self.lock = threading.Lock()
        
        # Token storage
        self.storage = TokenStorage()
        
        # Load existing token if available
        self._load_token_from_storage()
        
        # Log configuration status
        self._log_configuration_status()
    
    def get_valid_token(self) -> Optional[str]:
        """
        Get a valid access token, prioritizing manual token over OAuth2
        
        Returns:
            str: Valid access token, or None if unable to obtain
        """
        with self.lock:
            # PRIORITY 1: Check for manual token first
            manual_token = settings.powerbi_manual_token
            if manual_token:
                auth_logger.info("Using manual POWERBI_TOKEN from environment")
                return manual_token
            
            # PRIORITY 2: Try OAuth2 if manual token not available
            if not self._has_oauth_config():
                auth_logger.warning("No manual token and OAuth2 not configured")
                return None
            
            # Check if current token is valid
            if not self._is_token_expired():
                auth_logger.debug("Using valid OAuth2 token")
                return self.access_token
            
            # Token is expired or missing, try to refresh/get new one
            if self._refresh_access_token():
                return self.access_token
            else:
                auth_logger.error("Failed to obtain valid OAuth2 token")
                return None
    
    def invalidate_token(self) -> None:
        """Invalidate the current token (force refresh on next request)"""
        with self.lock:
            self.access_token = None
            self.token_expires_at = None
            self.storage.clear_token()
            auth_logger.info("Token invalidated")
    
    def get_token_info(self) -> Dict[str, Any]:
        """Get information about the current token"""
        with self.lock:
            # Check for manual token first
            manual_token = settings.powerbi_manual_token
            if manual_token:
                return {
                    "status": "Valid",
                    "type": "Manual Bearer Token",
                    "expires_at": "Never (manual token)",
                    "has_refresh_token": False,
                    "oauth_configured": self._has_oauth_config(),
                    "using_manual_token": True
                }
            
            # OAuth2 token info
            if not self.access_token:
                return {
                    "status": "No token",
                    "type": "OAuth2",
                    "oauth_configured": self._has_oauth_config(),
                    "using_manual_token": False
                }
            
            status = "Expired" if self._is_token_expired() else "Valid"
            
            return {
                "status": status,
                "type": "OAuth2",
                "expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
                "has_refresh_token": bool(self.refresh_token),
                "oauth_configured": self._has_oauth_config(),
                "using_manual_token": False
            }
    
    def _has_oauth_config(self) -> bool:
        """Check if OAuth2 configuration is complete"""
        return bool(self.client_id and self.client_secret and self.tenant_id)
    
    def _is_token_expired(self) -> bool:
        """Check if the current token is expired or will expire soon"""
        if not self.access_token or not self.token_expires_at:
            return True
        
        # Consider token expired if it expires within 5 minutes
        return datetime.now() >= (self.token_expires_at - timedelta(minutes=5))
    
    def _load_token_from_storage(self) -> bool:
        """Load token from storage"""
        try:
            token_data = self.storage.load_token()
            if not token_data:
                return False
            
            # Check if token is expired
            if self.storage.is_token_expired(token_data):
                auth_logger.debug("Stored token is expired")
                return False
            
            # Load token data
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            expires_str = token_data.get('expires_at')
            if expires_str:
                self.token_expires_at = datetime.fromisoformat(expires_str)
            
            auth_logger.info("Loaded valid token from storage")
            return True
            
        except Exception as e:
            auth_logger.error(f"Failed to load token from storage: {e}")
            return False
    
    def _request_new_token(self) -> bool:
        """Request a new access token using client credentials flow"""
        try:
            auth_logger.info("Requesting new OAuth2 token...")
            
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': self.scope
            }
            
            response = requests.post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Update instance state
            self.access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            
            # Save token
            self.storage.save_token(token_data)
            
            auth_logger.info("Successfully obtained new OAuth2 token")
            return True
            
        except requests.exceptions.RequestException as e:
            auth_logger.error(f"OAuth2 token request failed: {e}")
            return False
        except Exception as e:
            auth_logger.error(f"Unexpected error getting token: {e}")
            return False
    
    def _refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            auth_logger.debug("No refresh token available, requesting new token")
            return self._request_new_token()
        
        try:
            auth_logger.info("Refreshing OAuth2 token...")
            
            data = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token
            }
            
            response = requests.post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Update instance state
            self.access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            
            # Update refresh token if provided
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']
            
            # Save token
            self.storage.save_token(token_data)
            
            auth_logger.info("Successfully refreshed OAuth2 token")
            return True
            
        except requests.exceptions.RequestException as e:
            auth_logger.warning(f"Token refresh failed: {e}")
            auth_logger.info("Attempting to get new token...")
            return self._request_new_token()
        except Exception as e:
            auth_logger.error(f"Unexpected error refreshing token: {e}")
            return False
    
    def _log_configuration_status(self) -> None:
        """Log OAuth2 configuration status"""
        if not self._has_oauth_config():
            missing = []
            if not self.client_id:
                missing.append("POWERBI_CLIENT_ID")
            if not self.client_secret:
                missing.append("POWERBI_CLIENT_SECRET") 
            if not self.tenant_id:
                missing.append("POWERBI_TENANT_ID")
            
            auth_logger.warning(f"OAuth2 Warning: Missing environment variables: {', '.join(missing)}")
            auth_logger.info("Falling back to manual token mode")
        else:
            auth_logger.debug("OAuth2 configuration complete")


# Global token manager instance
_token_manager: Optional[PowerBITokenManager] = None


def get_token_manager() -> PowerBITokenManager:
    """Get the global token manager instance"""
    global _token_manager
    if _token_manager is None:
        _token_manager = PowerBITokenManager()
    return _token_manager


def get_powerbi_token() -> Optional[str]:
    """Convenience function to get a valid Power BI token"""
    return get_token_manager().get_valid_token()