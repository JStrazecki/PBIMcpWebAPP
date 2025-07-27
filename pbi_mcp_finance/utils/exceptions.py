"""
Custom exceptions for Power BI MCP Finance Server
"""


class PowerBIError(Exception):
    """Base exception for Power BI related errors"""
    pass


class AuthenticationError(PowerBIError):
    """Authentication or authorization related errors"""
    pass


class TokenExpiredError(AuthenticationError):
    """Token has expired and needs refresh"""
    pass


class WorkspaceNotFoundError(PowerBIError):
    """Power BI workspace not found"""
    pass


class DatasetNotFoundError(PowerBIError):
    """Power BI dataset not found"""
    pass


class DAXQueryError(PowerBIError):
    """DAX query execution error"""
    pass


class DatabaseConnectionError(Exception):
    """Database connection or operation error"""
    pass


class ConfigurationError(Exception):
    """Configuration validation error"""
    pass


class MeasureNotFoundError(PowerBIError):
    """Financial measure not found"""
    pass