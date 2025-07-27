"""
Configuration management for Power BI MCP Finance Server
"""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """Centralized configuration management"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.parent.parent.absolute()
        self.shared_dir = self.script_dir / "shared"
        self.shared_dir.mkdir(exist_ok=True)
    
    # Database Paths
    @property
    def conversation_db_path(self) -> Path:
        return self.shared_dir / "conversation_db.sqlite"
    
    @property
    def metrics_db_path(self) -> Path:
        return self.shared_dir / "mcp_metrics.sqlite"
    
    @property
    def optimization_db_path(self) -> Path:
        return self.shared_dir / "optimization_history.sqlite"
    
    # Authentication Configuration
    @property
    def powerbi_client_id(self) -> Optional[str]:
        return os.environ.get("POWERBI_CLIENT_ID")
    
    @property
    def powerbi_client_secret(self) -> Optional[str]:
        return os.environ.get("POWERBI_CLIENT_SECRET")
    
    @property
    def powerbi_tenant_id(self) -> Optional[str]:
        return os.environ.get("POWERBI_TENANT_ID")
    
    @property
    def powerbi_manual_token(self) -> Optional[str]:
        return os.environ.get("POWERBI_TOKEN")
    
    # Power BI Configuration - No hardcoded defaults
    @property
    def default_workspace_name(self) -> Optional[str]:
        return os.environ.get("POWERBI_WORKSPACE")
    
    @property
    def default_workspace_id(self) -> Optional[str]:
        return os.environ.get("POWERBI_WORKSPACE_ID")
    
    @property
    def default_dataset_name(self) -> Optional[str]:
        return os.environ.get("POWERBI_DATASET")
    
    def has_default_workspace_config(self) -> bool:
        """Check if default workspace configuration is available"""
        return bool(self.default_workspace_name and self.default_dataset_name)
    
    # API Configuration
    @property
    def powerbi_api_base_url(self) -> str:
        return "https://api.powerbi.com/v1.0/myorg"
    
    @property
    def fabric_api_base_url(self) -> str:
        return "https://api.fabric.microsoft.com/v1"
    
    # Monitoring Configuration
    @property
    def dashboard_port(self) -> int:
        return int(os.environ.get("DASHBOARD_PORT", "5555"))
    
    @property
    def dashboard_refresh_interval(self) -> int:
        return int(os.environ.get("DASHBOARD_REFRESH_MS", "5000"))
    
    # Token Storage Configuration
    @property
    def token_file_path(self) -> Path:
        return self.shared_dir / "powerbi_token.json"
    
    # OAuth2 Configuration
    @property
    def oauth_scope(self) -> str:
        return "https://analysis.windows.net/powerbi/api/.default"
    
    @property
    def oauth_token_url(self) -> str:
        tenant_id = self.powerbi_tenant_id or "common"
        return f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    def validate_oauth_config(self) -> bool:
        """Check if OAuth2 configuration is complete"""
        return all([
            self.powerbi_client_id,
            self.powerbi_client_secret,
            self.powerbi_tenant_id
        ])
    
    def has_manual_token(self) -> bool:
        """Check if manual token is available"""
        return bool(self.powerbi_manual_token)


# Global settings instance
settings = Settings()