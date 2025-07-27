"""
Token storage utilities for Power BI authentication
"""

import json
import keyring
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from ..config.settings import settings
from ..utils.logging import auth_logger
from ..utils.exceptions import AuthenticationError


class TokenStorage:
    """Handles secure token storage and retrieval"""
    
    def __init__(self):
        self.token_file = settings.token_file_path
        self.keyring_service = "powerbi_oauth"
        self.keyring_username = "token_data"
    
    def save_token(self, token_data: Dict[str, Any]) -> bool:
        """Save token to both file and keyring storage"""
        try:
            # Calculate expiration time
            expires_in = token_data.get('expires_in', 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
            
            # Prepare data for storage
            storage_data = {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'expires_at': expires_at.isoformat(),
                'retrieved_at': datetime.now().isoformat()
            }
            
            # Save to file (development)
            self._save_to_file(storage_data)
            
            # Save to keyring (production)
            self._save_to_keyring(storage_data)
            
            auth_logger.info(f"Token saved, expires at: {expires_at}")
            return True
            
        except Exception as e:
            auth_logger.error(f"Failed to save token: {e}")
            return False
    
    def load_token(self) -> Optional[Dict[str, Any]]:
        """Load token from storage (file first, then keyring)"""
        # Try file first
        token_data = self._load_from_file()
        if token_data:
            return token_data
        
        # Try keyring
        token_data = self._load_from_keyring()
        if token_data:
            return token_data
        
        return None
    
    def clear_token(self) -> bool:
        """Clear token from all storage locations"""
        success = True
        
        # Clear file
        try:
            if self.token_file.exists():
                self.token_file.unlink()
                auth_logger.debug("Token file deleted")
        except Exception as e:
            auth_logger.warning(f"Failed to delete token file: {e}")
            success = False
        
        # Clear keyring
        try:
            keyring.delete_password(self.keyring_service, self.keyring_username)
            auth_logger.debug("Token cleared from keyring")
        except Exception as e:
            auth_logger.warning(f"Failed to clear keyring: {e}")
            success = False
        
        return success
    
    def _save_to_file(self, storage_data: Dict[str, Any]) -> bool:
        """Save token data to file"""
        try:
            # Ensure parent directory exists
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.token_file, 'w') as f:
                json.dump(storage_data, f, indent=2)
            
            auth_logger.debug("Token saved to file")
            return True
        except Exception as e:
            auth_logger.error(f"Failed to save token to file: {e}")
            return False
    
    def _save_to_keyring(self, storage_data: Dict[str, Any]) -> bool:
        """Save token data to keyring"""
        try:
            keyring.set_password(
                self.keyring_service, 
                self.keyring_username, 
                json.dumps(storage_data)
            )
            auth_logger.debug("Token saved to keyring")
            return True
        except Exception as e:
            auth_logger.warning(f"Failed to save to keyring: {e}")
            return False
    
    def _load_from_file(self) -> Optional[Dict[str, Any]]:
        """Load token data from file"""
        try:
            if not self.token_file.exists():
                return None
            
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
            
            # Validate data structure
            if self._validate_token_data(token_data):
                auth_logger.debug("Token loaded from file")
                return token_data
            else:
                auth_logger.warning("Invalid token data in file")
                return None
                
        except Exception as e:
            auth_logger.error(f"Failed to load token from file: {e}")
            return None
    
    def _load_from_keyring(self) -> Optional[Dict[str, Any]]:
        """Load token data from keyring"""
        try:
            token_json = keyring.get_password(self.keyring_service, self.keyring_username)
            if not token_json:
                return None
            
            token_data = json.loads(token_json)
            
            # Validate data structure
            if self._validate_token_data(token_data):
                auth_logger.debug("Token loaded from keyring")
                return token_data
            else:
                auth_logger.warning("Invalid token data in keyring")
                return None
                
        except Exception as e:
            auth_logger.error(f"Failed to load token from keyring: {e}")
            return None
    
    def _validate_token_data(self, token_data: Dict[str, Any]) -> bool:
        """Validate token data structure"""
        required_keys = ['access_token', 'expires_at']
        return all(key in token_data for key in required_keys)
    
    def is_token_expired(self, token_data: Dict[str, Any]) -> bool:
        """Check if token is expired"""
        try:
            expires_str = token_data.get('expires_at')
            if not expires_str:
                return True
            
            expires_at = datetime.fromisoformat(expires_str)
            # Consider token expired if it expires within 5 minutes
            return datetime.now() >= (expires_at - timedelta(minutes=5))
        except Exception:
            return True