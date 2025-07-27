"""
MCP tools for financial statement analysis using Mapping table hierarchy
"""

from fastmcp import FastMCP
from typing import Dict, Any, List

from ...powerbi.client import get_powerbi_client
from ...config.settings import settings
from ...config.constants import POHODA_TABLES
from ...utils.logging import mcp_logger
from ...utils.exceptions import PowerBIError


def register_financial_statement_tools(mcp: FastMCP):
    """Register financial statement analysis tools that use Mapping table hierarchy"""
    
    
