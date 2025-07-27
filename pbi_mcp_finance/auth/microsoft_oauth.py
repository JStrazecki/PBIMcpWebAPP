"""
Microsoft Azure AD OAuth2 authentication module for MCP server
Provides OAuth2 flow using authlib for Microsoft Azure AD integration
"""

import os
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from functools import wraps
from flask import Flask, request, session, redirect, url_for, jsonify, Response
from authlib.integrations.flask_client import OAuth
from authlib.common.errors import AuthlibBaseError

from ..utils.logging import get_logger

logger = get_logger("microsoft_oauth")


class SessionStorage:
    """In-memory session storage for JWT tokens"""
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._cleanup_threshold = 100
    
    def create_session(self, user_id: str, token_data: Dict[str, Any], expires_in: int = 3600) -> str:
        """Create a new session and return session ID"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        self._sessions[session_id] = {
            'user_id': user_id,
            'token_data': token_data,
            'created_at': datetime.utcnow(),
            'expires_at': expires_at,
            'last_accessed': datetime.utcnow()
        }
        
        self._cleanup_expired()
        logger.debug(f"Created session {session_id} for user {user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by session ID"""
        if session_id not in self._sessions:
            return None
        
        session_data = self._sessions[session_id]
        
        # Check if session is expired
        if datetime.utcnow() > session_data['expires_at']:
            self.delete_session(session_id)
            return None
        
        # Update last accessed time
        session_data['last_accessed'] = datetime.utcnow()
        return session_data
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug(f"Deleted session {session_id}")
            return True
        return False
    
    def extend_session(self, session_id: str, additional_seconds: int = 3600) -> bool:
        """Extend session expiration time"""
        if session_id not in self._sessions:
            return False
        
        self._sessions[session_id]['expires_at'] += timedelta(seconds=additional_seconds)
        return True
    
    def _cleanup_expired(self):
        """Clean up expired sessions"""
        if len(self._sessions) < self._cleanup_threshold:
            return
        
        now = datetime.utcnow()
        expired_sessions = [
            sid for sid, data in self._sessions.items()
            if now > data['expires_at']
        ]
        
        for sid in expired_sessions:
            del self._sessions[sid]
        
        if expired_sessions:
            logger.debug(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self._sessions)


class MicrosoftOAuth:
    """Microsoft Azure AD OAuth2 authentication handler"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.oauth = OAuth()
        self.session_storage = SessionStorage()
        self._configure_oauth()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize OAuth with Flask app"""
        self.app = app
        self.oauth.init_app(app)
        self._register_routes()
    
    def _configure_oauth(self):
        """Configure OAuth client"""
        self.client_id = os.environ.get('AZURE_CLIENT_ID')
        self.client_secret = os.environ.get('AZURE_CLIENT_SECRET')
        self.tenant_id = os.environ.get('AZURE_TENANT_ID')
        self.redirect_uri = os.environ.get('AZURE_REDIRECT_URI', 'http://localhost:8000/auth/callback')
        
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            logger.warning("Microsoft OAuth not fully configured - missing environment variables")
            return
        
        # Microsoft OAuth endpoints
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.auth_url = f"{self.authority}/oauth2/v2.0/authorize"
        self.token_url = f"{self.authority}/oauth2/v2.0/token"
        
        # Register OAuth client
        self.oauth.register(
            name='microsoft',
            client_id=self.client_id,
            client_secret=self.client_secret,
            server_metadata_url=f"{self.authority}/v2.0/.well-known/openid_configuration",
            client_kwargs={
                'scope': 'openid profile email User.Read'
            }
        )
        
        logger.info("Microsoft OAuth configured successfully")
    
    def _register_routes(self):
        """Register OAuth routes with Flask app"""
        if not self.app:
            return
        
        @self.app.route('/auth/login')
        def login():
            return self._handle_login()
        
        @self.app.route('/auth/callback')
        def callback():
            return self._handle_callback()
        
        @self.app.route('/auth/logout')
        def logout():
            return self._handle_logout()
        
        @self.app.route('/auth/status')
        def status():
            return self._handle_status()
    
    def _handle_login(self) -> Response:
        """Handle login request"""
        if not self._is_configured():
            return jsonify({'error': 'OAuth not configured'}), 500
        
        try:
            microsoft = self.oauth.create_client('microsoft')
            redirect_uri = url_for('callback', _external=True)
            
            # Store state in session for CSRF protection
            session['oauth_state'] = secrets.token_urlsafe(32)
            
            return microsoft.authorize_redirect(
                redirect_uri,
                state=session['oauth_state']
            )
        except AuthlibBaseError as e:
            logger.error(f"OAuth login error: {e}")
            return jsonify({'error': 'Login failed'}), 500
    
    def _handle_callback(self) -> Response:
        """Handle OAuth callback"""
        if not self._is_configured():
            return jsonify({'error': 'OAuth not configured'}), 500
        
        try:
            # Verify state parameter
            if request.args.get('state') != session.get('oauth_state'):
                return jsonify({'error': 'Invalid state parameter'}), 400
            
            microsoft = self.oauth.create_client('microsoft')
            token = microsoft.authorize_access_token()
            
            # Get user info
            user_info = microsoft.get('https://graph.microsoft.com/v1.0/me').json()
            
            # Create session
            session_id = self.session_storage.create_session(
                user_id=user_info.get('id', 'unknown'),
                token_data={
                    'access_token': token['access_token'],
                    'refresh_token': token.get('refresh_token'),
                    'id_token': token.get('id_token'),
                    'user_info': user_info
                }
            )
            
            # Set session cookie
            session['session_id'] = session_id
            session['user_id'] = user_info.get('id')
            session['user_name'] = user_info.get('displayName', 'Unknown User')
            
            logger.info(f"User {user_info.get('displayName')} authenticated successfully")
            
            return self._get_success_html(user_info.get('displayName', 'User'))
            
        except AuthlibBaseError as e:
            logger.error(f"OAuth callback error: {e}")
            return jsonify({'error': 'Authentication failed'}), 500
    
    def _handle_logout(self) -> Response:
        """Handle logout request"""
        session_id = session.get('session_id')
        if session_id:
            self.session_storage.delete_session(session_id)
        
        session.clear()
        logger.info("User logged out")
        
        return jsonify({'message': 'Logged out successfully'})
    
    def _handle_status(self) -> Response:
        """Handle authentication status request"""
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'authenticated': False})
        
        session_data = self.session_storage.get_session(session_id)
        if not session_data:
            return jsonify({'authenticated': False})
        
        user_info = session_data['token_data'].get('user_info', {})
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user_info.get('id'),
                'name': user_info.get('displayName'),
                'email': user_info.get('mail') or user_info.get('userPrincipalName')
            },
            'session_expires': session_data['expires_at'].isoformat()
        })
    
    def _is_configured(self) -> bool:
        """Check if OAuth is properly configured"""
        return all([self.client_id, self.client_secret, self.tenant_id])
    
    def _get_success_html(self, user_name: str) -> str:
        """Get success page HTML"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; 
                       margin: 0; padding: 40px; background: #f5f5f5; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; 
                             padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .success {{ color: #28a745; font-size: 48px; text-align: center; margin-bottom: 20px; }}
                h1 {{ color: #333; text-align: center; margin-bottom: 10px; }}
                p {{ color: #666; text-align: center; line-height: 1.5; }}
                .user {{ color: #0066cc; font-weight: 600; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✅</div>
                <h1>Authentication Successful</h1>
                <p>Welcome, <span class="user">{user_name}</span>!</p>
                <p>You have been successfully authenticated with Microsoft Azure AD.</p>
                <p>You can now close this window and continue using the MCP server.</p>
            </div>
        </body>
        </html>
        """
    
    def get_user_token(self, session_id: str) -> Optional[str]:
        """Get access token for a session"""
        session_data = self.session_storage.get_session(session_id)
        if not session_data:
            return None
        
        return session_data['token_data'].get('access_token')
    
    def is_session_valid(self, session_id: str) -> bool:
        """Check if session is valid"""
        return self.session_storage.get_session(session_id) is not None


# Global OAuth instance
_oauth_instance: Optional[MicrosoftOAuth] = None


def get_oauth_instance() -> MicrosoftOAuth:
    """Get the global OAuth instance"""
    global _oauth_instance
    if _oauth_instance is None:
        _oauth_instance = MicrosoftOAuth()
    return _oauth_instance


def require_auth(f):
    """Decorator to require authentication for MCP tool functions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if authentication is enabled
        if not os.environ.get('AUTH_ENABLED', '').lower() in ('true', '1', 'yes'):
            # Authentication disabled - allow access
            return f(*args, **kwargs)
        
        oauth_instance = get_oauth_instance()
        
        # Check if OAuth is configured
        if not oauth_instance._is_configured():
            logger.warning("Authentication required but OAuth not configured")
            raise Exception("Authentication required but not configured")
        
        # Get session from Flask session
        session_id = session.get('session_id')
        if not session_id or not oauth_instance.is_session_valid(session_id):
            raise Exception("Authentication required - please login at /auth/login")
        
        return f(*args, **kwargs)
    
    return decorated_function