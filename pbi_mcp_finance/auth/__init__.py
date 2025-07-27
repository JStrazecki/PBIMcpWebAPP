"""
Authentication module for Power BI MCP Finance Server
Provides OAuth2 authentication and authorization utilities
"""

import os
from typing import Optional
from flask import session

from .microsoft_oauth import get_oauth_instance, require_auth
from .oauth_manager import get_token_manager, get_powerbi_token


def is_authenticated() -> bool:
    """
    Check if the current user is authenticated
    
    Returns:
        bool: True if user is authenticated, False otherwise
    """
    # If authentication is disabled, always return True
    if not os.environ.get('AUTH_ENABLED', '').lower() in ('true', '1', 'yes'):
        return True
    
    oauth_instance = get_oauth_instance()
    
    # Check if OAuth is configured
    if not oauth_instance._is_configured():
        return False
    
    # Check session
    session_id = session.get('session_id')
    if not session_id:
        return False
    
    return oauth_instance.is_session_valid(session_id)


def get_current_user() -> Optional[dict]:
    """
    Get current authenticated user information
    
    Returns:
        dict: User information if authenticated, None otherwise
    """
    if not is_authenticated():
        return None
    
    oauth_instance = get_oauth_instance()
    session_id = session.get('session_id')
    
    if not session_id:
        return None
    
    session_data = oauth_instance.session_storage.get_session(session_id)
    if not session_data:
        return None
    
    return session_data['token_data'].get('user_info')


def get_auth_token() -> Optional[str]:
    """
    Get authentication token for the current user
    
    Returns:
        str: Authentication token if available, None otherwise
    """
    if not is_authenticated():
        return None
    
    oauth_instance = get_oauth_instance()
    session_id = session.get('session_id')
    
    if session_id:
        return oauth_instance.get_user_token(session_id)
    
    return None


__all__ = [
    'is_authenticated',
    'get_current_user', 
    'get_auth_token',
    'require_auth',
    'get_oauth_instance',
    'get_token_manager',
    'get_powerbi_token'
]