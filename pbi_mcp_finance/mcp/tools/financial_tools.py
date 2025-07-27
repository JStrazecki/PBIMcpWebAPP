"""
MCP tools for financial analysis and reporting
"""

from fastmcp import FastMCP
from typing import Dict, Any

from ...powerbi.client import get_powerbi_client
from ...powerbi.utils import (
    build_revenue_analysis_dax, build_measure_query_dax, 
    validate_dimension, validate_measure_exists
)
from ...config.settings import settings
from ...config.constants import ACCOUNT_MAPS, FINANCIAL_MEASURES
from ...config.dynamic_measures import dynamic_measure_manager
from ...utils.logging import mcp_logger
from ...utils.formatters import format_financial_number
from ...utils.exceptions import PowerBIError, MeasureNotFoundError


def register_financial_tools(mcp: FastMCP):
    """Register financial analysis MCP tools"""
    
    
